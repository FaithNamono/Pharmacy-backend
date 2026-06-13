# ct_pharmacy/expenses/admin.py

from django.contrib import admin
from .models import ExpenseCategory, Expense

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'amount', 'date', 'payment_method', 'status', 'recorded_by')
    list_filter = ('category', 'payment_method', 'status', 'date')
    search_fields = ('description', 'vendor_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def expense_id(self, obj):
        return f"EXP-{obj.id}"
    expense_id.short_description = 'Expense ID'