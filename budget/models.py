from django.db import models
from django.contrib.auth.models import User
    

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_income = models.BooleanField(default=False)
    transaction_date = models.DateField()
    recurring = models.BooleanField(default=False)
    frequency = models.CharField(max_length=10, null=True, blank=True)  # e.g., 'monthly', 'weekly', 
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    original_transaction = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.description


