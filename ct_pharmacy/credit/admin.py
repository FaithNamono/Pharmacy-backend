# ct_pharmacy/credit/admin.py

from django.contrib import admin
from .models import Customer, CreditSale, CreditSaleItem, CreditPayment

class CreditSaleItemInline(admin.TabularInline):
    model = CreditSaleItem
    extra = 1
    fields = ['medicine', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    list_filter = ('created_at',)
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Name'

@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = ('credit_id', 'customer', 'total_amount', 'amount_paid', 'due_date', 'status', 'created_at')
    list_filter = ('status', 'due_date', 'created_at')
    search_fields = ('credit_id', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('credit_id', 'created_at')
    inlines = [CreditSaleItemInline]

@admin.register(CreditSaleItem)
class CreditSaleItemAdmin(admin.ModelAdmin):
    list_display = ('credit_sale', 'medicine', 'quantity', 'unit_price', 'total_price')
    list_filter = ('credit_sale__status',)
    search_fields = ('credit_sale__credit_id', 'medicine__name')

@admin.register(CreditPayment)
class CreditPaymentAdmin(admin.ModelAdmin):
    list_display = ('credit_sale', 'amount', 'payment_date', 'payment_method', 'received_by')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('credit_sale__credit_id', 'receipt_number')
    readonly_fields = ('payment_date',)