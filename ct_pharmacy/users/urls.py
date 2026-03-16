from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify-otp'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('reset-password-otp/', views.reset_password_with_otp, name='reset-password-otp'),
    path('users/', views.UserList.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetail.as_view(), name='user-detail'),
]