# ct_pharmacy/credit/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('customers/', views.CustomerList.as_view(), name='customer-list'),
    path('customers/<int:pk>/', views.CustomerDetail.as_view(), name='customer-detail'),
    path('sales/', views.CreditSaleList.as_view(), name='credit-sale-list'),
    path('sales/<int:pk>/', views.CreditSaleDetail.as_view(), name='credit-sale-detail'),
    path('sales/<int:credit_id>/payments/', views.record_payment, name='record-payment'),
    path('sales/<int:credit_id>/delete/', views.delete_credit_sale, name='delete-credit-sale'),
    path('summary/', views.credit_summary, name='credit-summary'),
]