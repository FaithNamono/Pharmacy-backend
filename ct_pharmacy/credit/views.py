# ct_pharmacy/credit/views.py

from django.db import models
from decimal import Decimal
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Customer, CreditSale, CreditSaleItem, CreditPayment
from .serializers import CustomerSerializer, CreditSaleSerializer, CreditPaymentSerializer

class CustomerList(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

class CustomerDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

class CreditSaleList(generics.ListCreateAPIView):
    queryset = CreditSale.objects.all()
    serializer_class = CreditSaleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('items', 'items__medicine')
        
        customer_id = self.request.query_params.get('customer')
        status_filter = self.request.query_params.get('status')

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def create(self, request, *args, **kwargs):
        # Get items from request
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response(
                {'error': 'At least one item is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate total amount
        total_amount = Decimal('0')
        for item in items_data:
            quantity = int(item.get('quantity', 0))
            unit_price = Decimal(str(item.get('unit_price', 0)))
            total_amount += quantity * unit_price
        
        # Create credit sale
        credit_sale = CreditSale.objects.create(
            customer_id=request.data.get('customer'),
            total_amount=total_amount,
            due_date=request.data.get('due_date'),
            notes=request.data.get('notes', ''),
            issued_by=request.user,
            amount_paid=Decimal('0'),
            status='pending'
        )
        
        # Create items
        for item in items_data:
            CreditSaleItem.objects.create(
                credit_sale=credit_sale,
                medicine_id=item.get('medicine'),
                quantity=item.get('quantity'),
                unit_price=Decimal(str(item.get('unit_price', 0)))
            )
        
        serializer = self.get_serializer(credit_sale)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CreditSaleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CreditSale.objects.all()
    serializer_class = CreditSaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def destroy(self, request, *args, **kwargs):
        credit_sale = self.get_object()
        
        # Check if credit sale has payments
        if credit_sale.payments.exists():
            return Response(
                {'error': 'Cannot delete credit sale with existing payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete associated items first
        credit_sale.items.all().delete()
        
        # Delete the credit sale
        credit_sale.delete()
        
        return Response(
            {'message': 'Credit sale deleted successfully'},
            status=status.HTTP_200_OK
        )

class CreditPaymentList(generics.ListCreateAPIView):
    queryset = CreditPayment.objects.all()
    serializer_class = CreditPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        credit_sale_id = self.request.query_params.get('credit_sale')
        if credit_sale_id:
            queryset = queryset.filter(credit_sale_id=credit_sale_id)
        return queryset

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def record_payment(request, credit_id):
    try:
        credit_sale = CreditSale.objects.get(id=credit_id)
    except CreditSale.DoesNotExist:
        return Response({'error': 'Credit sale not found'}, status=status.HTTP_404_NOT_FOUND)
    
    amount = request.data.get('amount')
    payment_method = request.data.get('payment_method', 'cash')
    notes = request.data.get('notes', '')
    
    if not amount:
        return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = Decimal(str(amount))
    except (TypeError, ValueError):
        return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
    
    if amount <= 0:
        return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
    
    if amount > credit_sale.balance:
        return Response({'error': f'Amount exceeds balance. Balance: {credit_sale.balance}'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Create payment
    payment = CreditPayment.objects.create(
        credit_sale=credit_sale,
        amount=amount,
        payment_method=payment_method,
        received_by=request.user,
        notes=notes
    )
    
    # Update credit sale
    credit_sale.amount_paid = credit_sale.amount_paid + amount
    
    if credit_sale.amount_paid >= credit_sale.total_amount:
        credit_sale.status = 'paid'
    elif credit_sale.amount_paid > 0:
        credit_sale.status = 'partially_paid'
    
    credit_sale.save()
    
    serializer = CreditPaymentSerializer(payment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def credit_summary(request):
    total_credit = CreditSale.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = CreditSale.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_outstanding = total_credit - total_paid
    overdue_count = CreditSale.objects.filter(
        due_date__lt=timezone.now().date(),
        status__in=['pending', 'partially_paid']
    ).count()
    
    return Response({
        'total_credit': float(total_credit),
        'total_paid': float(total_paid),
        'total_outstanding': float(total_outstanding),
        'overdue_count': overdue_count,
    })

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_credit_sale(request, credit_id):
    try:
        credit_sale = CreditSale.objects.get(id=credit_id)
    except CreditSale.DoesNotExist:
        return Response({'error': 'Credit sale not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if credit sale has payments
    if credit_sale.payments.exists():
        return Response(
            {'error': 'Cannot delete credit sale with existing payments'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete associated items
    credit_sale.items.all().delete()
    
    # Delete the credit sale
    credit_sale.delete()
    
    return Response(
        {'message': 'Credit sale deleted successfully'},
        status=status.HTTP_200_OK
    )