from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from .models import StockCount, StockCountItem
from .serializers import StockCountSerializer
from ct_pharmacy.medicines.models import Medicine

class StockCountList(generics.ListCreateAPIView):
    queryset = StockCount.objects.all()
    serializer_class = StockCountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

class StockCountDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = StockCount.objects.all()
    serializer_class = StockCountSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def submit_stock_count(request, pk):
    try:
        stock_count = StockCount.objects.get(pk=pk)
    except StockCount.DoesNotExist:
        return Response({'error': 'Stock count not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if stock_count.status != 'in_progress':
        return Response({'error': 'Stock count is not in progress'}, status=status.HTTP_400_BAD_REQUEST)
    
    items_data = request.data.get('items', [])
    notes = request.data.get('notes', '')
    
    if not items_data:
        return Response({'error': 'No items data provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    variances = []
    
    for item_data in items_data:
        medicine_id = item_data.get('medicine_id')
        physical_quantity = item_data.get('physical_quantity')
        item_notes = item_data.get('notes', '')
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            continue
        
        # Get the existing count item or create
        count_item, created = StockCountItem.objects.get_or_create(
            stock_count=stock_count,
            medicine=medicine,
            defaults={
                'system_quantity': medicine.quantity,
                'physical_quantity': physical_quantity,
                'notes': item_notes
            }
        )
        
        if not created:
            count_item.physical_quantity = physical_quantity
            count_item.notes = item_notes
            count_item.save()
        
        if count_item.variance != 0:
            variances.append({
                'medicine': medicine.name,
                'system': count_item.system_quantity,
                'physical': count_item.physical_quantity,
                'variance': count_item.variance,
                'variance_value': float(count_item.variance_value)
            })
    
    stock_count.status = 'completed'
    if notes:
        stock_count.notes = notes
    stock_count.save()
    
    return Response({
        'stock_count_id': stock_count.count_id,
        'status': stock_count.status,
        'variances': variances
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_stock_count(request, pk):
    try:
        stock_count = StockCount.objects.get(pk=pk)
    except StockCount.DoesNotExist:
        return Response({'error': 'Stock count not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if stock_count.status != 'completed':
        return Response({'error': 'Stock count must be completed before verification'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Update medicine quantities based on the count
    for item in stock_count.items.all():
        medicine = item.medicine
        medicine.quantity = item.physical_quantity
        medicine.save()
    
    stock_count.status = 'verified'
    stock_count.verified_by = request.user
    stock_count.save()
    
    return Response({
        'stock_count_id': stock_count.count_id,
        'status': stock_count.status,
        'verified_by': request.user.get_full_name()
    })