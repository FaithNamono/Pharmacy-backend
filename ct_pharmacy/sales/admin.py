# ct_pharmacy/sales/admin.py

from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ['medicine', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_id', 'customer_name', 'user', 'total_amount', 'sale_date')
    list_filter = ('sale_date', 'payment_method', 'user')
    search_fields = ('sale_id', 'customer_name', 'user__username')
    readonly_fields = ('sale_id', 'sale_date')
    inlines = [SaleItemInline]

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'medicine', 'quantity', 'unit_price', 'total_price')
    search_fields = ('sale__sale_id', 'medicine__name')