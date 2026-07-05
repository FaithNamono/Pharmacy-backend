# ct_pharmacy/stock/admin.py

from django.contrib import admin
from .models import StockCount, StockCountItem

class StockCountItemInline(admin.TabularInline):
    model = StockCountItem
    extra = 1
    fields = ['medicine', 'system_quantity', 'physical_quantity', 'variance', 'notes']
    readonly_fields = ['variance']

@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ('count_id', 'count_date', 'counted_by', 'status')
    list_filter = ('status', 'count_date')
    search_fields = ('count_id', 'counted_by__username')
    
    readonly_fields = ('count_id', 'count_date')  # ✅ Fixed - removed 'created_at'
    inlines = [StockCountItemInline]
    
    fieldsets = (
        ('Stock Count Information', {
            'fields': ('count_id', 'count_date', 'counted_by', 'status')
        }),
        ('Verification', {
            'fields': ('verified_by', 'notes')
        }),
    )