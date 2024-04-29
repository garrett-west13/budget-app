from django.contrib import admin
from .models import Transaction, Category, Goal

# Register your models here.
admin.site.register(
    (Transaction, Category, Goal)
)
