from rest_framework import generics, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Sale
from .serializers import SaleSerializer

class SaleList(generics.ListCreateAPIView):
    queryset = Sale.objects.all().order_by('-sale_date')
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'medicine']
    search_fields = ['sale_id', 'medicine__name', 'user__username']
    ordering_fields = ['sale_date', 'total_price', 'quantity']

class SaleDetail(generics.RetrieveAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def daily_sales(request):
    today = timezone.now().date()
    sales = Sale.objects.filter(sale_date__date=today)
    total = sales.aggregate(
        total=Sum('total_price'),
        count=Count('id')
    )
    serializer = SaleSerializer(sales, many=True)
    return Response({
        'date': today,
        'total_sales': float(total['total'] or 0),
        'total_transactions': total['count'] or 0,
        'sales': serializer.data
    })