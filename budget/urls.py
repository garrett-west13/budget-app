from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('add_transaction/<int:year>/<int:month>/<int:day>', views.add_transaction, name='add_transaction'),
    path('calendar/<int:year>/<int:month>/', views.calendar, name='calendar'),
]
