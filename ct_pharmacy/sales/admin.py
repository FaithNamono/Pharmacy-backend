from django.contrib import admin
from .models import Sale

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_id', 'medicine', 'user', 'quantity', 'total_price', 'sale_date')
    list_filter = ('sale_date', 'user')
    search_fields = ('sale_id', 'medicine__name', 'user__username')
    readonly_fields = ('sale_id', 'total_price', 'sale_date')