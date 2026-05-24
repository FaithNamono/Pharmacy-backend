from django.contrib import admin
from .models import StockCount, StockCountItem

class StockCountItemInline(admin.TabularInline):
    model = StockCountItem
    extra = 1

@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ('count_id', 'count_date', 'counted_by', 'status')
    list_filter = ('status', 'count_date')
    inlines = [StockCountItemInline]