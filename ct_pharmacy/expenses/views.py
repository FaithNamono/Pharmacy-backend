from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import ExpenseCategory, Expense
from .serializers import ExpenseCategorySerializer, ExpenseSerializer
class ExpenseCategoryList(generics.ListCreateAPIView):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ExpenseCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ExpenseList(generics.ListCreateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        category = self.request.query_params.get('category')
        
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        if category:
            queryset = queryset.filter(category_id=category)
        
        return queryset

class ExpenseDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def expense_summary(request):
    # Current month
    now = timezone.now()
    start_of_month = now.replace(day=1).date()
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Total expenses this month
    monthly_expenses = Expense.objects.filter(
        payment_date__gte=start_of_month,
        payment_date__lte=end_of_month
    )
    monthly_total = monthly_expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Expenses by category
    expenses_by_category = monthly_expenses.values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Total all expenses
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    return Response({
        'total_expenses': float(total_expenses),
        'monthly_total': float(monthly_total),
        'expenses_by_category': [
            {
                'category': item['category__name'],
                'total': float(item['total']),
                'count': item['count']
            }
            for item in expenses_by_category
        ]
    })