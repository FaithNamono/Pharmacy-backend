from django.urls import path
from . import views

urlpatterns = [
    path('', views.SaleList.as_view(), name='sale-list'),
    path('<int:pk>/', views.SaleDetail.as_view(), name='sale-detail'),
    path('daily/', views.daily_sales, name='daily-sales'),
    path('items/<str:sale_id>/', views.sale_items, name='sale-items'),
]