# ct_pharmacy/sales/views.py

from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Sale
from .serializers import SaleSerializer, MultiItemSaleSerializer

class SaleList(generics.ListCreateAPIView):
    queryset = Sale.objects.all().order_by('-sale_date')
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'medicine']
    search_fields = ['sale_id', 'medicine__name', 'user__username']
    ordering_fields = ['sale_date', 'total_price', 'quantity']

    def create(self, request, *args, **kwargs):
        print("📦 REQUEST DATA:", request.data)
        
        if 'items' in request.data:
            serializer = MultiItemSaleSerializer(data=request.data)
            if serializer.is_valid():
                try:
                    sale = serializer.save()
                    return Response({
                        'success': True,
                        'data': {
                            'id': sale.id,
                            'sale_id': sale.sale_id,
                            'total_amount': sale.total_sale_amount,
                            'items_count': sale.items_count,
                            'sale_date': sale.sale_date,
                        }
                    }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    print("❌ ERROR:", str(e))
                    return Response({
                        'success': False,
                        'error': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                print("❌ SERIALIZER ERRORS:", serializer.errors)
                return Response({
                    'success': False,
                    'error': str(serializer.errors)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle single item sale
        return super().create(request, *args, **kwargs)

class SaleDetail(generics.RetrieveAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def daily_sales(request):
    today = timezone.now().date()
    sales = Sale.objects.filter(sale_date__date=today)
    
    total = sales.aggregate(total=Sum('total_price'), count=Count('id', distinct='sale_id'))
    
    serializer = SaleSerializer(sales, many=True)
    return Response({
        'date': today,
        'total_sales': float(total['total'] or 0),
        'total_transactions': total['count'] or 0,
        'sales': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sale_items(request, sale_id):
    sales = Sale.objects.filter(sale_id=sale_id).order_by('id')
    serializer = SaleSerializer(sales, many=True)
    return Response({
        'sale_id': sale_id,
        'items': serializer.data,
        'total_amount': float(sales.aggregate(total=Sum('total_price'))['total'] or 0),
        'items_count': sales.count()
    })

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_sale(request, sale_id):
    """
    Delete a sale and optionally return stock to inventory.
    URL: /api/sales/{sale_id}/delete/?return_stock=true
    """
    try:
        # Get all sales with this sale_id
        sales = Sale.objects.filter(sale_id=sale_id)
        
        if not sales.exists():
            return Response({
                'success': False,
                'error': f'Sale with ID {sale_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return Response({
                'success': False,
                'error': 'You must be logged in to delete sales'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get return_stock parameter (default: true)
        return_stock = request.query_params.get('return_stock', 'true').lower() == 'true'
        
        # Store sale details for response
        sale_id_value = sale_id
        total_amount = sales.aggregate(total=Sum('total_price'))['total'] or 0
        items_count = sales.count()
        restored_items = []
        
        # If return_stock is True, restore medicine quantities
        if return_stock:
            for sale in sales:
                medicine = sale.medicine
                medicine.quantity += sale.quantity
                medicine.save()
                restored_items.append({
                    'medicine': medicine.name,
                    'quantity_restored': sale.quantity
                })
            
            print(f"🔄 RESTORED STOCK for {len(restored_items)} items")
        
        # Store data before deletion
        sale_data = {
            'sale_id': sale_id_value,
            'total_amount': float(total_amount),
            'items_count': items_count,
            'stock_returned': return_stock,
            'restored_items': restored_items if return_stock else []
        }
        
        # Delete the sales
        sales.delete()
        
        return Response({
            'success': True,
            'message': f'Sale {sale_id_value} deleted successfully',
            'data': sale_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ DELETE SALE ERROR: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to delete sale: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_sale_by_id(request, sale_id):
    """
    Get all items for a specific sale_id
    """
    try:
        sales = Sale.objects.filter(sale_id=sale_id).order_by('id')
        
        if not sales.exists():
            return Response({
                'success': False,
                'error': f'Sale with ID {sale_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SaleSerializer(sales, many=True)
        total_amount = sales.aggregate(total=Sum('total_price'))['total'] or 0
        
        return Response({
            'success': True,
            'data': {
                'sale_id': sale_id,
                'items': serializer.data,
                'total_amount': float(total_amount),
                'items_count': sales.count(),
                'sale_date': sales.first().sale_date,
                'customer_name': sales.first().customer_name,
                'staff_name': sales.first().user.get_full_name() if sales.first().user else '',
                'payment_method': sales.first().payment_method,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)