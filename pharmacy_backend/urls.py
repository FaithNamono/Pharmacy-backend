"""
Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('ct_pharmacy.users.urls')),
    path('api/medicines/', include('ct_pharmacy.medicines.urls')),
    path('api/sales/', include('ct_pharmacy.sales.urls')),
    path('api/reports/', include('ct_pharmacy.reports.urls')),
    path('api/credit/', include('ct_pharmacy.credit.urls')),           
    path('api/expenses/', include('ct_pharmacy.expenses.urls')),       
    path('api/prescriptions/', include('ct_pharmacy.prescriptions.urls')),
    path('api/users/', include('ct_pharmacy.users.urls')),
    path('api/stock/', include('ct_pharmacy.stock.urls')),             
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)