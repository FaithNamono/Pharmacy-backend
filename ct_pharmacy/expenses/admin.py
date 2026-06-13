# ct_pharmacy/expenses/admin.py

from django.contrib import admin
from .models import ExpenseCategory, Expense

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_id', 'category', 'amount', 'payment_date', 'payment_method', 'recorded_by')
    list_filter = ('category', 'payment_method', 'payment_date')
    search_fields = ('expense_id', 'description', 'supplier__name')
    readonly_fields = ('expense_id', 'created_at')
    
    fieldsets = (
        ('Expense Information', {
            'fields': ('expense_id', 'category', 'supplier', 'description', 'amount')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'payment_date', 'receipt_number', 'recorded_by')
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at')
        }),
    )