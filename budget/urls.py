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
    path('transaction_list/', views.transaction_list, name='transaction_list'),
    path('recurring_transactions/', views.recurring_transactions, name='recurring_transactions'),
]
