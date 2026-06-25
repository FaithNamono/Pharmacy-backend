# ct_pharmacy/sales/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.SaleList.as_view(), name='sale-list'),
    path('<int:pk>/', views.SaleDetail.as_view(), name='sale-detail'),
    path('daily/', views.daily_sales, name='daily-sales'),
    path('items/<str:sale_id>/', views.sale_items, name='sale-items'),
    
    # ✅ NEW: Delete sale endpoint
    path('<str:sale_id>/delete/', views.delete_sale, name='delete-sale'),
    
    # ✅ NEW: Get sale by sale_id
    path('by-id/<str:sale_id>/', views.get_sale_by_id, name='get-sale-by-id'),
]