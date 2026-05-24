from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.ExpenseCategoryList.as_view(), name='expense-category-list'),
    path('categories/<int:pk>/', views.ExpenseCategoryDetail.as_view(), name='expense-category-detail'),
    path('', views.ExpenseList.as_view(), name='expense-list'),
    path('<int:pk>/', views.ExpenseDetail.as_view(), name='expense-detail'),
    path('summary/', views.expense_summary, name='expense-summary'),
]