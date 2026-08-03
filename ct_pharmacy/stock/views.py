# ct_pharmacy/stock/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import StockCount, StockCountItem, InventoryHistory
from .serializers import (
    StockCountSerializer, InventoryHistorySerializer, InventorySummarySerializer
)
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

# ✅ ADD THIS VIEWSET
class InventoryHistoryViewSet(ReadOnlyModelViewSet):
    """ViewSet for Inventory History"""
    queryset = InventoryHistory.objects.all()
    serializer_class = InventoryHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['medicine__name', 'reference', 'notes']
    ordering_fields = ['created_at', 'total_value']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by medicine
        medicine_id = self.request.query_params.get('medicine')
        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)
        
        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get inventory summary"""
        total_medicines = Medicine.objects.count()
        total_value = Medicine.objects.aggregate(
            total=Sum('quantity' * 'unit_cost')
        )['total'] or 0
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_activity = self.get_queryset().filter(created_at__gte=thirty_days_ago)
        
        total_restock_value = recent_activity.filter(
            action_type='restock'
        ).aggregate(total=Sum('total_value'))['total'] or 0
        
        total_sale_value = recent_activity.filter(
            action_type='sale'
        ).aggregate(total=Sum('total_value'))['total'] or 0
        
        data = {
            'total_medicines': total_medicines,
            'total_value': total_value,
            'total_restock_value': total_restock_value,
            'total_sale_value': total_sale_value,
            'recent_activity_count': recent_activity.count(),
        }
        
        serializer = InventorySummarySerializer(data)
        return Response(serializer.data)

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
        old_quantity = medicine.quantity
        new_quantity = item.physical_quantity
        quantity_changed = new_quantity - old_quantity
        
        # Create inventory history entry
        if quantity_changed != 0:
            InventoryHistory.objects.create(
                medicine=medicine,
                action_type='stock_take',
                quantity_changed=quantity_changed,
                previous_quantity=old_quantity,
                new_quantity=new_quantity,
                unit_cost=medicine.unit_cost,
                total_value=quantity_changed * medicine.unit_cost,
                reference=stock_count.count_id,
                notes=f"Stock take verification - {stock_count.count_id}",
                performed_by=request.user
            )
        
        medicine.quantity = new_quantity
        medicine.save()
    
    stock_count.status = 'verified'
    stock_count.verified_by = request.user
    stock_count.save()
    
    return Response({
        'stock_count_id': stock_count.count_id,
        'status': stock_count.status,
        'verified_by': request.user.get_full_name()
    })

# ✅ ADD THIS VIEW TO RECORD RESTOCK HISTORY
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def record_restock(request):
    """Record a restock and create inventory history"""
    items = request.data.get('items', [])
    notes = request.data.get('notes', '')
    reference = request.data.get('reference', f"RESTOCK-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    
    if not items:
        return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    created_entries = []
    total_value = 0
    
    for item_data in items:
        medicine_id = item_data.get('medicine_id')
        quantity = item_data.get('quantity')
        unit_cost = item_data.get('unit_cost')
        
        if not medicine_id or not quantity:
            continue
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            continue
        
        old_quantity = medicine.quantity
        new_quantity = old_quantity + quantity
        cost = unit_cost or medicine.unit_cost
        
        # Update medicine quantity
        medicine.quantity = new_quantity
        medicine.save()
        
        # Create inventory history entry
        history = InventoryHistory.objects.create(
            medicine=medicine,
            action_type='restock',
            quantity_changed=quantity,
            previous_quantity=old_quantity,
            new_quantity=new_quantity,
            unit_cost=cost,
            total_value=cost * quantity,
            reference=reference,
            notes=notes,
            performed_by=request.user
        )
        
        created_entries.append(history)
        total_value += history.total_value
    
    serializer = InventoryHistorySerializer(created_entries, many=True)
    return Response({
        'success': True,
        'message': f'Restocked {len(created_entries)} items',
        'total_value': total_value,
        'entries': serializer.data
    }, status=status.HTTP_201_CREATED)

# ✅ ADD THIS VIEW TO RECORD SALE HISTORY
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def record_sale_history(request):
    """Record a sale and create inventory history"""
    items = request.data.get('items', [])
    sale_id = request.data.get('sale_id', '')
    notes = request.data.get('notes', '')
    
    if not items:
        return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    created_entries = []
    total_value = 0
    
    for item_data in items:
        medicine_id = item_data.get('medicine_id')
        quantity = item_data.get('quantity')
        unit_price = item_data.get('unit_price')
        
        if not medicine_id or not quantity:
            continue
        
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            continue
        
        old_quantity = medicine.quantity
        new_quantity = old_quantity - quantity
        cost = medicine.unit_cost
        
        # Update medicine quantity
        medicine.quantity = new_quantity
        medicine.save()
        
        # Create inventory history entry
        history = InventoryHistory.objects.create(
            medicine=medicine,
            action_type='sale',
            quantity_changed=-quantity,
            previous_quantity=old_quantity,
            new_quantity=new_quantity,
            unit_cost=cost,
            total_value=cost * quantity,
            reference=sale_id,
            notes=f"Sale: {notes}",
            performed_by=request.user
        )
        
        created_entries.append(history)
        total_value += history.total_value
    
    serializer = InventoryHistorySerializer(created_entries, many=True)
    return Response({
        'success': True,
        'message': f'Recorded sale for {len(created_entries)} items',
        'total_value': total_value,
        'entries': serializer.data
    }, status=status.HTTP_201_CREATED)