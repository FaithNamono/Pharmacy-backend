from django.urls import path
from . import views

urlpatterns = [
    path('', views.MedicineList.as_view(), name='medicine-list'),
    path('<int:pk>/', views.MedicineDetail.as_view(), name='medicine-detail'),
    path('low-stock/', views.low_stock_medicines, name='low-stock'),
    path('expiring/', views.expiring_medicines, name='expiring'),
    path('expired/', views.expired_medicines, name='expired'),
    path('categories/', views.CategoryList.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetail.as_view(), name='category-detail'),
    path('suppliers/', views.SupplierList.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetail.as_view(), name='supplier-detail'),
]