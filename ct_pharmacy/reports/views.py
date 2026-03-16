from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, F, Q, Avg, Max, Min
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime
from ct_pharmacy.sales.models import Sale
from ct_pharmacy.medicines.models import Medicine
from ct_pharmacy.users.models import User
from ct_pharmacy.sales.serializers import SaleSerializer
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """Get summary statistics for dashboard"""
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    
    # Today's sales
    today_sales = Sale.objects.filter(sale_date__date=today)
    today_total = today_sales.aggregate(total=Sum('total_price'))['total'] or 0
    today_count = today_sales.count()
    
    # Month to date sales
    month_sales = Sale.objects.filter(sale_date__date__gte=first_day_of_month)
    month_total = month_sales.aggregate(total=Sum('total_price'))['total'] or 0
    
    # Stock alerts
    low_stock_count = Medicine.objects.filter(quantity__lte=F('min_stock_level')).count()
    expired_count = Medicine.objects.filter(expiry_date__lt=today).count()
    expiring_count = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    ).count()
    
    # Total medicines
    total_medicines = Medicine.objects.count()
    total_sales = Sale.objects.count()
    
    return Response({
        'today': {
            'sales_total': float(today_total),
            'transactions': today_count,
        },
        'month_to_date': {
            'sales_total': float(month_total),
        },
        'alerts': {
            'low_stock': low_stock_count,
            'expired': expired_count,
            'expiring_soon': expiring_count,
        },
        'totals': {
            'medicines': total_medicines,
            'sales': total_sales,
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request):
    """Comprehensive sales report with filters"""
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    staff_id = request.GET.get('staff_id')
    period = request.GET.get('period', 'day')
    
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Base queryset
    sales = Sale.objects.filter(
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date
    )
    
    if staff_id:
        sales = sales.filter(user_id=staff_id)
    
    # Group by period
    if period == 'day':
        sales_by_period = sales.annotate(
            period=TruncDay('sale_date')
        ).values('period').annotate(
            total=Sum('total_price'),
            count=Count('id')
        ).order_by('period')
    else:
        sales_by_period = sales.annotate(
            period=TruncMonth('sale_date')
        ).values('period').annotate(
            total=Sum('total_price'),
            count=Count('id')
        ).order_by('period')
    
    # Summary statistics
    total_sales = sales.aggregate(
        total=Sum('total_price'),
        avg=Avg('total_price'),
        max=Max('total_price'),
        min=Min('total_price'),
        count=Count('id')
    )
    
    # Top selling medicines
    top_medicines = sales.values(
        'medicine__id', 'medicine__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price'),
        transaction_count=Count('id')
    ).order_by('-total_revenue')[:10]
    
    # Sales by staff
    sales_by_staff = sales.values(
        'user__id', 'user__first_name', 'user__last_name', 'user__role'
    ).annotate(
        total=Sum('total_price'),
        transactions=Count('id'),
        avg_transaction=Sum('total_price') / Count('id')
    ).order_by('-total')
    
    return Response({
        'period': {
            'start_date': start_date,
            'end_date': end_date,
        },
        'summary': {
            'total_revenue': float(total_sales['total'] or 0),
            'total_transactions': total_sales['count'] or 0,
            'average_transaction': float(total_sales['avg'] or 0),
            'max_transaction': float(total_sales['max'] or 0),
            'min_transaction': float(total_sales['min'] or 0),
        },
        'sales_by_period': [
            {
                'period': item['period'],
                'total': float(item['total']),
                'count': item['count']
            }
            for item in sales_by_period
        ],
        'top_medicines': [
            {
                'id': item['medicine__id'],
                'name': item['medicine__name'],
                'total_quantity': item['total_quantity'],
                'total_revenue': float(item['total_revenue']),
                'transaction_count': item['transaction_count']
            }
            for item in top_medicines
        ],
        'sales_by_staff': [
            {
                'staff_id': item['user__id'],
                'name': f"{item['user__first_name']} {item['user__last_name']}",
                'role': item['user__role'],
                'total': float(item['total']),
                'transactions': item['transactions'],
                'avg_transaction': float(item['avg_transaction'])
            }
            for item in sales_by_staff
        ],
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_report(request):
    """Comprehensive inventory report"""
    today = timezone.now().date()
    
    # Stock status
    in_stock = Medicine.objects.filter(quantity__gt=F('min_stock_level'))
    low_stock = Medicine.objects.filter(
        quantity__gt=0,
        quantity__lte=F('min_stock_level')
    )
    out_of_stock = Medicine.objects.filter(quantity=0)
    
    # Expiry status
    valid = Medicine.objects.filter(expiry_date__gt=today + timedelta(days=30))
    expiring_soon = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    )
    expired = Medicine.objects.filter(expiry_date__lt=today)
    
    # Category breakdown
    by_category = Medicine.objects.values(
        'category__name'
    ).annotate(
        total_items=Count('id'),
        total_value=Sum(F('quantity') * F('price')),
        avg_price=Avg('price')
    )
    
    # Supplier breakdown
    by_supplier = Medicine.objects.values(
        'supplier__name'
    ).annotate(
        total_items=Count('id'),
        total_value=Sum(F('quantity') * F('price')),
    )
    
    # Inventory value
    total_value = Medicine.objects.aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or 0
    
    return Response({
        'summary': {
            'total_medicines': Medicine.objects.count(),
            'total_value': float(total_value),
            'in_stock': in_stock.count(),
            'low_stock': low_stock.count(),
            'out_of_stock': out_of_stock.count(),
            'valid': valid.count(),
            'expiring_soon': expiring_soon.count(),
            'expired': expired.count(),
        },
        'by_category': [
            {
                'category': item['category__name'],
                'total_items': item['total_items'],
                'total_value': float(item['total_value'] or 0),
                'avg_price': float(item['avg_price'] or 0)
            }
            for item in by_category
        ],
        'by_supplier': [
            {
                'supplier': item['supplier__name'],
                'total_items': item['total_items'],
                'total_value': float(item['total_value'] or 0),
            }
            for item in by_supplier
        ],
        'low_stock_items': [
            {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'min_stock_level': item.min_stock_level,
                'price': float(item.price)
            }
            for item in low_stock
        ],
        'expired_items': [
            {
                'id': item.id,
                'name': item.name,
                'expiry_date': item.expiry_date,
                'quantity': item.quantity,
                'price': float(item.price)
            }
            for item in expired
        ],
        'expiring_items': [
            {
                'id': item.id,
                'name': item.name,
                'expiry_date': item.expiry_date,
                'quantity': item.quantity,
                'price': float(item.price)
            }
            for item in expiring_soon
        ],
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_performance_report(request):
    """Staff performance report"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    # Sales by staff
    sales_data = Sale.objects.filter(
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date
    ).values(
        'user__id', 'user__first_name', 'user__last_name', 'user__role'
    ).annotate(
        total_sales=Sum('total_price'),
        transaction_count=Count('id'),
        avg_transaction=Sum('total_price') / Count('id'),
        unique_medicines=Count('medicine', distinct=True),
    ).order_by('-total_sales')
    
    return Response({
        'period': {
            'start_date': start_date,
            'end_date': end_date,
        },
        'staff_summary': [
            {
                'staff_id': item['user__id'],
                'name': f"{item['user__first_name']} {item['user__last_name']}",
                'role': item['user__role'],
                'total_sales': float(item['total_sales'] or 0),
                'transaction_count': item['transaction_count'],
                'avg_transaction': float(item['avg_transaction'] or 0),
                'unique_medicines': item['unique_medicines']
            }
            for item in sales_data
        ],
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_sales_report(request):
    """Daily sales report"""
    date = request.GET.get('date', timezone.now().date())
    
    sales = Sale.objects.filter(sale_date__date=date)
    total_sales = sales.aggregate(total=Sum('total_price'))['total'] or 0
    total_transactions = sales.count()
    
    # Sales by staff
    sales_by_staff = sales.values(
        'user__id', 'user__first_name', 'user__last_name'
    ).annotate(
        total=Sum('total_price'),
        count=Count('id')
    ).order_by('-total')
    
    return Response({
        'date': date,
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'sales_by_staff': sales_by_staff,
        'sales': SaleSerializer(sales, many=True).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def low_stock_report(request):
    """Low stock report"""
    low_stock_medicines = Medicine.objects.filter(
        quantity__lte=F('min_stock_level')
    ).values(
        'id', 'name', 'quantity', 'min_stock_level', 'price'
    )
    
    return Response({
        'total_low_stock': low_stock_medicines.count(),
        'medicines': low_stock_medicines
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expired_report(request):
    """Expired medicines report"""
    expired = Medicine.objects.filter(
        expiry_date__lt=timezone.now().date()
    ).values(
        'id', 'name', 'batch_number', 'quantity', 'expiry_date', 'price'
    ).order_by('expiry_date')
    
    return Response({
        'total_expired': expired.count(),
        'medicines': expired
    })