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

    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'description', 'transaction_date', 'recurring', 'is_income', 'end_date']
        widgets = {
            'recurring': forms.CheckboxInput(),
            'is_income': forms.RadioSelect(choices=[(True, 'Income'), (False, 'Expense')]),
            'transaction_date': forms.DateInput(attrs={ 'value': datetime.now().date(), 'hidden': True, 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        # Calculate default end date (one year from the current date)
        default_end_date = datetime.now() + timedelta(days=365)
        # Set default end date as initial value for the end_date field
        self.initial['end_date'] = default_end_date.strftime('%Y-%m-%d')
        # Remove the 'required' attribute from the end_date field
        self.fields['end_date'].required = False
        self.initial['transaction_date'] = datetime.now().date()
