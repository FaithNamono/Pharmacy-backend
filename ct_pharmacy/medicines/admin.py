from django.contrib import admin
from .models import Category, Supplier, Medicine

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')  # phone and email will show blank if empty
    search_fields = ('name', 'contact_person')
    list_filter = ()  # Remove filters that might cause issues with null values

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'category', 
        'retail_price', 
        'wholesale_price',
        'quantity', 
        'expiry_date', 
        'is_low_stock'
    )
    list_filter = ('category', 'supplier', 'expiry_date', 'unit_type')
    search_fields = ('name', 'generic_name', 'batch_number', 'barcode')
    list_editable = ('retail_price', 'wholesale_price', 'quantity')
    readonly_fields = ('created_at', 'updated_at', 'unit_cost')
    
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