import json
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
from django.db.models import Sum, F
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
    date = datetime(year, month, day)

    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.transaction_date = date
            category_id = form.cleaned_data.get('category')

            if not category_id:
                messages.error(request, 'Please select an existing category.')
                return render(request, 'add_transaction.html', {'form': form})

            if transaction.recurring:
                end_date = form.cleaned_data.get('end_date')
                if end_date and end_date <= transaction.transaction_date.date():
                    messages.error(request, 'End date cannot be earlier than transaction date.')
                    return render(request, 'add_transaction.html', {'form': form})

                if 'frequency' in form.cleaned_data and transaction.recurring:
                    transaction.frequency = form.cleaned_data['frequency']
                    transaction.start_date = transaction.transaction_date

            transaction.save()
            messages.success(request, 'Transaction added successfully.')
            return redirect('add_transaction', year=year, month=month, day=day)        

    else:
        form = TransactionForm(request.user, initial={'transaction_date': date})

    transactions = Transaction.objects.filter(user=request.user, transaction_date=date)
    income_transactions = transactions.filter(is_income=True)
    expense_transactions = transactions.filter(is_income=False)
    total_income = income_transactions.aggregate(total=Sum('amount'))['total'] or 0
    total_expense = expense_transactions.aggregate(total=Sum('amount'))['total'] or 0
    balance = total_income - total_expense
    savings = expense_transactions.filter(category__name='Savings').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'transaction_date': date,
        'form': form,
        'income_transactions': income_transactions,
        'expense_transactions': expense_transactions,
        'total_income': total_income,
        'total_expenses': total_expense,
        'balance': balance,
        'savings': savings,
    }

    return render(request, 'transactions.html', context)


@login_required
def create_category(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            category_name = data.get('name')

            # Validate category_name (e.g., check for empty string)
            if not category_name:
                raise ValueError('Category name is missing or empty')

            # Create a new category
            category = Category.objects.create(name=category_name, user=request.user)

            # Return a success response with the created category data
            return JsonResponse({'id': category.id, 'name': category.name})

        except Exception as e:
            # Return an error response with an appropriate message
            return JsonResponse({'error': str(e)}, status=400)

    else:
        # Return a method not allowed response if the request method is not POST
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        

def calendar(request, year, month):
    calendar = Calendar()
    calendar_html = calendar.formatmonth(year, month)
    return HttpResponse(calendar_html)
    
