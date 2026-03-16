from django.contrib import admin
from .models import Category, Supplier, Medicine

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'contact_person')

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'quantity', 'expiry_date', 'is_low_stock')
    list_filter = ('category', 'supplier', 'expiry_date')
    search_fields = ('name', 'generic_name', 'batch_number')
    list_editable = ('price', 'quantity')