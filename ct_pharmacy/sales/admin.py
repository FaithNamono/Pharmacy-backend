# ct_pharmacy/sales/admin.py

from django.contrib import admin
from .models import Sale

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_id', 'medicine', 'quantity', 'total_price', 'customer_name', 'sale_type', 'sale_date')
    list_filter = ('sale_type', 'payment_method', 'sale_date')
    search_fields = ('sale_id', 'customer_name', 'medicine__name', 'user__username')
    readonly_fields = ('sale_id', 'subtotal', 'discount_amount', 'total_price', 'sale_date')
    
    fieldsets = (
        ('Sale Information', {
            'fields': ('sale_id', 'medicine', 'quantity', 'sale_type', 'customer_name')
        }),
        ('Pricing', {
            'fields': ('unit_cost', 'unit_price', 'discount_percentage', 'discount_amount', 'subtotal', 'total_price')
        }),
        ('Additional Info', {
            'fields': ('user', 'prescription', 'payment_method', 'notes', 'sale_date')
        }),
    )