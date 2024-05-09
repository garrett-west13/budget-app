from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('add_transaction/<int:year>/<int:month>/<int:day>', views.add_transaction, name='add_transaction'),
    path('calendar/<int:year>/<int:month>/', views.calendar, name='calendar'),
    path('create_category/', views.create_category, name='create_category'),
    path('transaction_list/<int:year>/<int:month>/', views.transaction_list, name='transaction_list'),
    path('recurring_transaction_detail/<int:pk>/', views.recurring_transaction_detail, name='recurring_transaction_detail'),
    path('store_selected_month_year/', views.store_selected_month_year, name='store_selected_month_year'),
    path('calculate_totals/', views.calculate_totals, name='calculate_totals'),
    path('update_transaction/<int:pk>/', views.update_transaction, name='update_transaction'),
    path('delete_transaction/<int:pk>/', views.delete_transaction, name='delete_transaction'),
    path('category_list/', views.category_list, name='category_list'),
    path('category_detail/<int:pk>/', views.category_detail, name='category_detail'),
    path('delete_category/<int:pk>/', views.delete_category, name='delete_category'),
    path('yearly_summary/<int:year>/', views.yearly_summary, name='yearly_summary'),
]
