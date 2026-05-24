from rest_framework import generics, permissions, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
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