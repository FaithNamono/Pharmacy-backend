# ct_pharmacy/medicines/admin.py

from django.contrib import admin
from .models import Category, Supplier, Medicine

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'retail_price', 'wholesale_price', 'quantity', 'expiry_date')
    list_filter = ('category', 'expiry_date', 'unit_type')
    search_fields = ('name', 'generic_name', 'batch_number', 'barcode')
    list_editable = ('retail_price', 'wholesale_price', 'quantity')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'generic_name', 'category', 'supplier', 'description')
        }),
        ('Pricing', {
            'fields': ('unit_cost', 'wholesale_price', 'retail_price', 'discount_percentage')
        }),
        ('Stock Information', {
            'fields': ('quantity', 'min_stock_level', 'unit_type', 'units_per_pack')
        }),
        ('Expiry & Batch', {
            'fields': ('expiry_date', 'batch_number', 'barcode')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )