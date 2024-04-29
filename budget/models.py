from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class User(AbstractUser):
    groups = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='budget_user_groups')
    user_permissions = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='budget_user_permissions')

    def __str__(self):
        return self.username
    

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    recurring = models.BooleanField(default=False)
    is_income = models.BooleanField(default=False)
    transaction_date = models.DateField()

    def __str__(self):
        return self.description


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateField()

    def __str__(self):
        return self.name

