# ct_pharmacy/reports/views.py - COMPLETE FIXED VERSION

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, F, Avg, Max, Min, Q
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone
from datetime import timedelta, datetime

from ct_pharmacy.sales.models import Sale
from ct_pharmacy.medicines.models import Medicine
from ct_pharmacy.sales.serializers import SaleSerializer
from ct_pharmacy.credit.models import CreditSale
from ct_pharmacy.expenses.models import Expense
from ct_pharmacy.prescriptions.models import Prescription



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """Get summary statistics for dashboard"""

    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)

    # Today's sales
    today_sales = Sale.objects.filter(sale_date__date=today)

    today_total = today_sales.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    today_count = today_sales.count()

    # Month sales
    month_sales = Sale.objects.filter(
        sale_date__date__gte=first_day_of_month
    )

    month_total = month_sales.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Credit sales summary
    total_credit = CreditSale.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    total_credit_paid = CreditSale.objects.aggregate(
        paid=Sum('amount_paid')
    )['paid'] or 0
    
    total_credit_outstanding = total_credit - total_credit_paid

    # Alerts
    low_stock_count = Medicine.objects.filter(
        quantity__lte=F('min_stock_level')
    ).count()

    expired_count = Medicine.objects.filter(
        expiry_date__lt=today
    ).count()

    expiring_count = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    ).count()

    return Response({
        'today': {
            'sales_total': float(today_total),
            'transactions': today_count,
        },
        'month_to_date': {
            'sales_total': float(month_total),
        },
        'credit_summary': {
            'total_credit': float(total_credit),
            'total_paid': float(total_credit_paid),
            'total_outstanding': float(total_credit_outstanding),
        },
        'alerts': {
            'low_stock': low_stock_count,
            'expired': expired_count,
            'expiring_soon': expiring_count,
        },
        'totals': {
            'medicines': Medicine.objects.count(),
            'sales': Sale.objects.count(),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request):
    """Comprehensive sales report including credit sales"""

    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    staff_id = request.GET.get('staff_id')
    period = request.GET.get('period', 'day')

    # Default dates
    if not end_date:
        end_date = timezone.now().date()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    if not start_date:
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    # Cash Sales
    cash_sales = Sale.objects.filter(
        sale_date__date__gte=start_date,
        sale_date__date__lte=end_date
    )

    # Credit Sales
    credit_sales = CreditSale.objects.filter(
        due_date__gte=start_date,
        due_date__lte=end_date
    )

    if staff_id:
        cash_sales = cash_sales.filter(user_id=staff_id)

    # Cash sales summary
    cash_summary = cash_sales.aggregate(
        total=Sum('total_price'),
        avg=Avg('total_price'),
        max=Max('total_price'),
        min=Min('total_price'),
        count=Count('id')
    )

    # Credit sales summary
    credit_summary = credit_sales.aggregate(
        total=Sum('total_amount'),
        total_paid=Sum('amount_paid'),
        total_balance=Sum(F('total_amount') - F('amount_paid')),
        count=Count('id')
    )

    # Get max values safely
    cash_max = cash_summary['max'] or 0
    credit_max = credit_summary['total'] or 0  # Use total as fallback since credit doesn't have max
    max_transaction = max(float(cash_max), float(credit_max))

    # Get min values safely
    cash_min = cash_summary['min'] or 999999
    min_transaction = float(cash_min) if cash_min != 999999 else 0

    # Total revenue including credit
    total_revenue = (cash_summary['total'] or 0) + (credit_summary['total'] or 0)
    total_transactions = (cash_summary['count'] or 0) + (credit_summary['count'] or 0)

    # Cash sales by period
    if period == 'month':
        cash_by_period = cash_sales.annotate(
            period=TruncMonth('sale_date')
        ).values('period').annotate(
            total=Sum('total_price'),
            count=Count('id')
        ).order_by('period')
    else:
        cash_by_period = cash_sales.annotate(
            period=TruncDay('sale_date')
        ).values('period').annotate(
            total=Sum('total_price'),
            count=Count('id')
        ).order_by('period')

    # Credit sales by period (by due date)
    if period == 'month':
        credit_by_period = credit_sales.annotate(
            period=TruncMonth('due_date')
        ).values('period').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('period')
    else:
        credit_by_period = credit_sales.annotate(
            period=TruncDay('due_date')
        ).values('period').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('period')

    # Top medicines (cash sales only)
    top_medicines = cash_sales.values(
        'medicine__id',
        'medicine__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price'),
        transaction_count=Count('id')
    ).order_by('-total_revenue')[:10]

    # Staff performance (cash sales only)
    sales_by_staff = cash_sales.values(
        'user__id',
        'user__first_name',
        'user__last_name',
        'user__role'
    ).annotate(
        total=Sum('total_price'),
        transactions=Count('id'),
        avg_transaction=Avg('total_price')
    ).order_by('-total')

    # Credit sales by customer
    credit_by_customer = credit_sales.values(
        'customer__id',
        'customer__first_name',
        'customer__last_name'
    ).annotate(
        total=Sum('total_amount'),
        paid=Sum('amount_paid'),
        balance=Sum(F('total_amount') - F('amount_paid')),
        count=Count('id')
    ).order_by('-total')

    # Prepare response data safely
    cash_sales_data = {
        'total': float(cash_summary['total'] or 0),
        'transactions': cash_summary['count'] or 0,
        'average': float(cash_summary['avg'] or 0),
        'max': float(cash_summary['max'] or 0),
        'min': float(cash_summary['min'] or 0),
        'sales_by_period': [
            {
                'period': item['period'],
                'total': float(item['total'] or 0),
                'count': item['count']
            }
            for item in cash_by_period
        ],
    }

    credit_sales_data = {
        'total': float(credit_summary['total'] or 0),
        'total_paid': float(credit_summary['total_paid'] or 0),
        'total_balance': float(credit_summary['total_balance'] or 0),
        'transactions': credit_summary['count'] or 0,
        'sales_by_period': [
            {
                'period': item['period'],
                'total': float(item['total'] or 0),
                'count': item['count']
            }
            for item in credit_by_period
        ],
        'by_customer': [
            {
                'customer_id': item['customer__id'],
                'customer_name': f"{item['customer__first_name']} {item['customer__last_name']}",
                'total': float(item['total'] or 0),
                'paid': float(item['paid'] or 0),
                'balance': float(item['balance'] or 0),
                'count': item['count']
            }
            for item in credit_by_customer
        ],
    }

    return Response({
        'period': {
            'start_date': start_date,
            'end_date': end_date,
        },
        'summary': {
            'total_revenue': float(total_revenue),
            'total_transactions': total_transactions,
            'average_transaction': float(total_revenue / total_transactions if total_transactions > 0 else 0),
            'max_transaction': max_transaction,
            'min_transaction': min_transaction,
        },
        'cash_sales': cash_sales_data,
        'credit_sales': credit_sales_data,
        'top_medicines': [
            {
                'id': item['medicine__id'],
                'name': item['medicine__name'],
                'total_quantity': item['total_quantity'],
                'total_revenue': float(item['total_revenue'] or 0),
                'transaction_count': item['transaction_count']
            }
            for item in top_medicines
        ],
        'sales_by_staff': [
            {
                'staff_id': item['user__id'],
                'name': f"{item['user__first_name']} {item['user__last_name']}",
                'role': item['user__role'],
                'total': float(item['total'] or 0),
                'transactions': item['transactions'],
                'avg_transaction': float(item['avg_transaction'] or 0)
            }
            for item in sales_by_staff
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_report(request):
    """Inventory report"""
    
    today = timezone.now().date()
    
    # All medicines (including expired) for total count
    all_medicines = Medicine.objects.all()
    
    # Non-expired medicines only (for stock status)
    active_medicines = Medicine.objects.exclude(expiry_date__lt=today)
    
    # Stock status (only non-expired medicines)
    in_stock = active_medicines.filter(
        quantity__gt=F('min_stock_level')
    )
    
    low_stock = active_medicines.filter(
        quantity__gt=0,
        quantity__lte=F('min_stock_level')
    )
    
    out_of_stock = active_medicines.filter(
        quantity=0
    )
    
    # Expiry status (all medicines)
    valid = Medicine.objects.filter(
        expiry_date__gt=today + timedelta(days=30)
    )
    
    expiring_soon = Medicine.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    )
    
    expired = Medicine.objects.filter(
        expiry_date__lt=today
    )
    
    # Total inventory value (only active/non-expired)
    total_value = active_medicines.aggregate(
        total=Sum(
            F('quantity') * F('retail_price')
        )
    )['total'] or 0
    
    # Total value including expired
    total_value_with_expired = all_medicines.aggregate(
        total=Sum(
            F('quantity') * F('retail_price')
        )
    )['total'] or 0
    
    # Category summary (only active/non-expired)
    by_category = active_medicines.values(
        'category__name'
    ).annotate(
        total_items=Count('id'),
        total_value=Sum(
            F('quantity') * F('retail_price')
        ),
        avg_price=Avg('retail_price')
    )
    
    # Supplier summary (only active/non-expired)
    by_supplier = active_medicines.values(
        'supplier__name'
    ).annotate(
        total_items=Count('id'),
        total_value=Sum(
            F('quantity') * F('retail_price')
        )
    )
    
    return Response({
        'summary': {
            'total_medicines': all_medicines.count(),  # Includes expired
            'total_active_medicines': active_medicines.count(),  # Excludes expired
            'total_value': float(total_value),  # Excludes expired
            'total_value_with_expired': float(total_value_with_expired),  # Includes expired
            'in_stock': in_stock.count(),
            'low_stock': low_stock.count(),
            'out_of_stock': out_of_stock.count(),
            'valid': valid.count(),
            'expiring_soon': expiring_soon.count(),
            'expired': expired.count(),
        },
        'by_category': [
            {
                'category': item['category__name'] or 'Uncategorized',
                'total_items': item['total_items'],
                'total_value': float(item['total_value'] or 0),
                'avg_price': float(item['avg_price'] or 0)
            }
            for item in by_category
        ],
        'by_supplier': [
            {
                'supplier': item['supplier__name'] or 'Unknown',
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
                'retail_price': float(item.retail_price),
                'unit_cost': float(item.unit_cost) if item.unit_cost else 0,
                'supplier': item.supplier.name if item.supplier else None,
                'category': item.category.name if item.category else None,
                'expiry_date': item.expiry_date,
            }
            for item in low_stock
        ],
        'expired_items': [
            {
                'id': item.id,
                'name': item.name,
                'expiry_date': item.expiry_date,
                'quantity': item.quantity,
                'retail_price': float(item.retail_price),
                'batch_number': item.batch_number,
            }
            for item in expired
        ],
        'expiring_items': [
            {
                'id': item.id,
                'name': item.name,
                'expiry_date': item.expiry_date,
                'quantity': item.quantity,
                'retail_price': float(item.retail_price),
                'days_remaining': (item.expiry_date - today).days,
                'batch_number': item.batch_number,
            }
            for item in expiring_soon
        ],
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_performance_report(request):
    """Staff performance report including expenses, prescriptions, and credit sales"""

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

    # Get all staff members
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get all active users
    staff_users = User.objects.filter(is_active=True)

    staff_summary = []

    # Print debug info
    print(f"📊 Period: {start_date} to {end_date}")

    for staff in staff_users:
        # Cash sales
        cash_sales = Sale.objects.filter(
            user=staff,
            sale_date__date__gte=start_date,
            sale_date__date__lte=end_date
        )
        
        # ✅ FIXED: Filter credit sales by created_at, NOT due_date
        credit_sales = CreditSale.objects.filter(
            issued_by=staff,
            created_at__date__gte=start_date,  # Changed from due_date
            created_at__date__lte=end_date      # Changed from due_date
        )
        
        # Debug print credit sales per staff
        print(f"📊 Staff {staff.username} (ID: {staff.id}): Credit sales count = {credit_sales.count()}")
        
        # Expenses recorded by this staff
        expenses = Expense.objects.filter(
            recorded_by=staff,
            payment_date__gte=start_date,
            payment_date__lte=end_date
        )
        
        # Prescriptions created by this staff
        prescriptions = Prescription.objects.filter(
            created_by=staff,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        total_cash_sales = cash_sales.aggregate(total=Sum('total_price'))['total'] or 0
        transaction_count = cash_sales.count()
        avg_transaction = total_cash_sales / transaction_count if transaction_count > 0 else 0
        unique_medicines = cash_sales.values('medicine').distinct().count()
        
        total_credit_sales = credit_sales.aggregate(total=Sum('total_amount'))['total'] or 0
        total_credit_collected = credit_sales.aggregate(total=Sum('amount_paid'))['total'] or 0
        credit_count = credit_sales.count()
        
        total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
        expense_count = expenses.count()
        prescription_count = prescriptions.count()

        total_sales = total_cash_sales + total_credit_sales
        net_contribution = total_sales - total_expenses

        # Include staff who have ANY activity
        if total_cash_sales > 0 or total_credit_sales > 0 or total_expenses > 0 or prescription_count > 0:
            staff_summary.append({
                'staff_id': staff.id,
                'name': staff.get_full_name() or staff.username,
                'role': 'admin' if staff.is_superuser else 'staff',
                'total_cash_sales': float(total_cash_sales),
                'total_credit_sales': float(total_credit_sales),
                'total_credit_collected': float(total_credit_collected),
                'total_sales': float(total_sales),
                'transaction_count': transaction_count,
                'credit_count': credit_count,
                'avg_transaction': float(avg_transaction),
                'unique_medicines': unique_medicines,
                'total_expenses': float(total_expenses),
                'expense_count': expense_count,
                'prescription_count': prescription_count,
                'net_contribution': float(net_contribution),
            })
            
            print(f"📊 {staff.username}: Cash={total_cash_sales}, Credit={total_credit_sales}, Expenses={total_expenses}")

    # Sort by net contribution (highest first)
    staff_summary.sort(key=lambda x: x['net_contribution'], reverse=True)

    return Response({
        'period': {
            'start_date': start_date,
            'end_date': end_date,
        },
        'staff_summary': staff_summary,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_sales_report(request):
    """Daily sales report"""

    report_date = request.GET.get(
        'date',
        str(timezone.now().date())
    )

    sales = Sale.objects.filter(
        sale_date__date=report_date
    )

    total_sales = sales.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    total_transactions = sales.count()

    sales_by_staff = sales.values(
        'user__id',
        'user__first_name',
        'user__last_name'
    ).annotate(
        total=Sum('total_price'),
        count=Count('id')
    ).order_by('-total')

    return Response({
        'date': report_date,
        'total_sales': float(total_sales),
        'total_transactions': total_transactions,
        'sales_by_staff': [
            {
                'staff_id': item['user__id'],
                'name': f"{item['user__first_name']} {item['user__last_name']}",
                'total': float(item['total'] or 0),
                'count': item['count']
            }
            for item in sales_by_staff
        ],
        'sales': SaleSerializer(sales, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def low_stock_report(request):
    """Low stock medicines"""

    medicines = Medicine.objects.filter(
        quantity__lte=F('min_stock_level')
    ).values(
        'id',
        'name',
        'quantity',
        'min_stock_level',
        'retail_price'
    )

    return Response({
        'total_low_stock': medicines.count(),
        'medicines': list(medicines)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expired_report(request):
    """Expired medicines"""

    expired = Medicine.objects.filter(
        expiry_date__lt=timezone.now().date()
    ).values(
        'id',
        'name',
        'batch_number',
        'quantity',
        'expiry_date',
        'retail_price'
    ).order_by('expiry_date')

    return Response({
        'total_expired': expired.count(),
        'medicines': list(expired)
    })