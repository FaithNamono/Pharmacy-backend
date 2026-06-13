# ct_pharmacy/stock/admin.py

from django.contrib import admin
from .models import StockCount, StockCountItem

class StockCountItemInline(admin.TabularInline):
    model = StockCountItem
    extra = 1
    fields = ['medicine', 'system_quantity', 'actual_quantity', 'difference']

@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ('id', 'count_date', 'counted_by', 'status')
    list_filter = ('status', 'count_date')
    search_fields = ('counted_by__username',)
    readonly_fields = ('created_at',)
    inlines = [StockCountItemInline]