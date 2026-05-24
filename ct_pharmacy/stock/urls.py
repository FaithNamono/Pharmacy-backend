from django.urls import path
from . import views

urlpatterns = [
    path('counts/', views.StockCountList.as_view(), name='stock-count-list'),
    path('counts/<int:pk>/', views.StockCountDetail.as_view(), name='stock-count-detail'),
    path('counts/<int:pk>/submit/', views.submit_stock_count, name='submit-stock-count'),
    path('counts/<int:pk>/verify/', views.verify_stock_count, name='verify-stock-count'),
]