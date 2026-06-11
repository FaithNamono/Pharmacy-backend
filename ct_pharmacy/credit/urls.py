# ct_pharmacy/credit/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Customers
    path('customers/', views.CustomerList.as_view(), name='customer-list'),
    path('customers/<int:pk>/', views.CustomerDetail.as_view(), name='customer-detail'),
    path('customers/<int:customer_id>/summary/', views.customer_credit_summary, name='customer-credit-summary'),
    
    # Credit Sales
    path('sales/', views.CreditSaleList.as_view(), name='credit-sale-list'),
    path('sales/<int:pk>/', views.CreditSaleDetail.as_view(), name='credit-sale-detail'),
    path('sales/<int:credit_id>/pay/', views.record_payment, name='record-payment'),  # ✅ Keep this
    path('sales/<int:credit_id>/payments/', views.record_payment, name='record-payment-alt'),  # ✅ Add this alias
    path('sales/<int:credit_id>/delete/', views.delete_credit_sale, name='delete-credit-sale'),
    
    # Payments
    path('payments/', views.CreditPaymentList.as_view(), name='credit-payment-list'),
    
    # Summary
    path('summary/', views.credit_summary, name='credit-summary'),
]