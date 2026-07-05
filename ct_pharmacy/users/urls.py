# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('current-user/', views.get_current_user, name='current_user'),
    path('change-password/', views.change_password, name='change-password'),
    path('', views.get_all_users, name='get_all_users'),           # GET /api/users/
    path('', views.create_user, name='create_user'),               # POST /api/users/
    path('<int:user_id>/', views.update_user, name='update_user'), # PUT /api/users/{id}/
    path('<int:user_id>/', views.delete_user, name='delete_user'), # DELETE /api/users/{id}/

]