# ct_pharmacy/stock/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'history', views.InventoryHistoryViewSet, basename='inventoryhistory')

urlpatterns = [
    # Stock Count endpoints
    path('counts/', views.StockCountList.as_view(), name='stock-count-list'),
    path('counts/<int:pk>/', views.StockCountDetail.as_view(), name='stock-count-detail'),
    path('counts/<int:pk>/submit/', views.submit_stock_count, name='submit-stock-count'),
    path('counts/<int:pk>/verify/', views.verify_stock_count, name='verify-stock-count'),
    
    # Inventory History endpoints
    path('', include(router.urls)),
    
    # Restock and Sale history endpoints
    path('record-restock/', views.record_restock, name='record-restock'),
    path('record-sale/', views.record_sale_history, name='record-sale-history'),
]