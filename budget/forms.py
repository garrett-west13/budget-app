from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Transaction

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
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'description', 'transaction_date', 'recurring', 'is_income']
        widgets = {
            'recurring': forms.CheckboxInput(),
            'is_income': forms.RadioSelect(choices=[(True, 'Income'), (False, 'Expense')]),
        }

    def save(self, commit=True):
        transaction = super().save(commit=False)
        transaction.user = str(transaction.user)  # Convert user to string
        if commit:
            transaction.save()
        return transaction   