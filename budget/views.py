from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, TransactionForm
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .calendar import Calendar
from datetime import datetime
from .models import Transaction, Category, Goal
from django.http import JsonResponse
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta


@login_required
def index(request):
    currentYear = datetime.now().year
    currentMonth = datetime.now().month

    # Fetch dynamic data for monthly overview
    total_expenses = Transaction.objects.filter(date__year=currentYear, date__month=currentMonth).aggregate(Sum('amount'))['amount__sum']
    total_income = 0  
    total_expenses = total_expenses or 0  
    total_balance = total_income - total_expenses
    total_savings = 0  

    context = {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'total_balance': total_balance,
        'total_savings': total_savings,
    }

    return render(request, 'index.html', context)




def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            if User.objects.filter(username=username).exists():
                # Username already exists, display error message
                messages.error(request, 'This username is already taken. Please choose a different one.')
            else:
                # Username is unique, save the form
                form.save()
                messages.success(request, f'Account created for {username}. You can now log in.')
                return redirect('login')
        else:
            # Form data is invalid, display error message
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def add_transaction(request, year, month, day):
    # Convert year, month, day to integers
    year = int(year)
    month = int(month)
    day = int(day)

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.transaction_date = datetime(year, month, day)
            transaction.frequency = form.cleaned_data['frequency']
            transaction.save()

            # Check if the transaction is recurring and handle it
            if transaction.recurring:
                current_date = transaction.transaction_date
                end_date = transaction.end_date or current_date + timedelta(days=365)  # Default to one year from transaction date
                while current_date <= end_date:
                    current_date += relativedelta(months=1)
                    new_transaction = Transaction(
                        user=request.user,
                        amount=transaction.amount,
                        category=transaction.category,
                        description=transaction.description,
                        recurring=False, 
                        is_income=transaction.is_income,
                        transaction_date=current_date
                    )
                    new_transaction.save()

            # Redirect after saving
            return redirect('add_transaction', year=year, month=month, day=day)
    else:
        form = TransactionForm(initial={'transaction_date': datetime(year, month, day)})

    # Fetch all transactions for the current user and transaction date
    transactions = Transaction.objects.filter(user=request.user, transaction_date=datetime(year, month, day))

    # Separate income and expense transactions
    income_transactions = transactions.filter(is_income=True)
    expense_transactions = transactions.filter(is_income=False)

    # Calculate total income and expense
    total_income = income_transactions.aggregate(total=Sum('amount'))['total'] or 0
    total_expense = expense_transactions.aggregate(total=Sum('amount'))['total'] or 0
    remainder = total_income - total_expense
    total_savings = 0

    context = {
        'transaction_date': datetime(year, month, day),
        'form': form,
        'income_transactions': income_transactions,
        'expense_transactions': expense_transactions,
        'total_income': total_income,
        'total_expenses': total_expense,
        'total_balance': remainder,
        'total_savings': total_savings,
    }

    return render(request, 'transactions.html', context)



def calendar(request, year, month):
    calendar = Calendar()
    calendar_html = calendar.formatmonth(year, month)
    return HttpResponse(calendar_html)
    
