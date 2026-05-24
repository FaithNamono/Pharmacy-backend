from django.urls import path
from . import views

urlpatterns = [
    path('', views.PrescriptionList.as_view(), name='prescription-list'),
    path('<int:pk>/', views.PrescriptionDetail.as_view(), name='prescription-detail'),
    path('<int:pk>/fill/', views.fill_prescription, name='fill-prescription'),
]