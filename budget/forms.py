from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Transaction , Category
from datetime import datetime, timedelta

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):

    class Meta:
        model = User
        fields = ['username', 'password']

class TransactionForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)

    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'description', 'transaction_date', 'recurring', 'is_income', 'end_date', 'frequency', 'start_date']
        widgets = {
            'recurring': forms.CheckboxInput(attrs={}),
            'is_income': forms.RadioSelect(choices=[(True, 'Income'), (False, 'Expense')]),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'frequency': forms.Select(attrs={}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }
