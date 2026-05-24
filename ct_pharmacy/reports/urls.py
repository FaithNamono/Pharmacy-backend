# ct_pharmacy/reports/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_summary, name='dashboard-summary'),
    path('sales/', views.sales_report, name='sales-report'),
    path('inventory/', views.inventory_report, name='inventory-report'),
    path('staff/', views.staff_performance_report, name='staff-performance-report'),
    path('daily-sales/', views.daily_sales_report, name='daily-sales'),
    path('low-stock/', views.low_stock_report, name='low-stock'),
    path('expired/', views.expired_report, name='expired'),
]