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
from django.http import JsonResponse, Http404, HttpResponse
from django.db.models import Sum, F
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from django.urls import reverse


@login_required
def index(request):
    currentDate = datetime.now()
    currentYear = currentDate.year
    currentMonth = currentDate.month

    storedMonth = request.session.get('selectedMonth')
    storedYear = request.session.get('selectedYear')

    if storedMonth and storedYear:
        currentMonth = int(storedMonth)
        currentYear = int(storedYear)

    context = {
        'currentYear': currentYear,
        'currentMonth': currentMonth
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
    try:
        date = datetime(year, month, day)
    except ValueError:
        raise Http404("Invalid date")

    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user

            # Validate and set frequency and start date for recurring transactions
            if transaction.recurring:
                original_transaction = Transaction.objects.get(pk=transaction.pk)
                transaction.original_transaction = original_transaction
                end_date = form.cleaned_data.get('end_date')
                frequency = form.cleaned_data.get('frequency')
                if not end_date or not frequency:
                    messages.error(request, 'Please provide both end date and frequency for recurring transactions.')
                    return render(request, 'transactions.html', {'form': form})

                # Set the transaction's frequency and start date
                transaction.frequency = frequency
                transaction.start_date = date

                # Save the transaction
                transaction.save()

                messages.success(request, 'Recurring transaction added successfully.')
                return redirect('recurring_transactions')  # Redirect to transaction list view or any other appropriate URL
            else:
                # Process non-recurring transaction
                transaction.end_date = None
                transaction.save()
                messages.success(request, 'Transaction added successfully.')
                return redirect('add_transaction', year=year, month=month, day=day)

    else:
        form = TransactionForm(request.user, initial={'transaction_date': date})


    # Retrieve transactions for the selected date
    transactions = Transaction.objects.filter(user=request.user, transaction_date=date)
    income_transactions = transactions.filter(is_income=True)
    expense_transactions = transactions.filter(is_income=False)

    # Calculate total income, expenses, balance, and savings
    total_income = round(income_transactions.aggregate(total=Sum('amount'))['total'] or 0, 2)
    total_expense = round(expense_transactions.aggregate(total=Sum('amount'))['total'] or 0, 2)
    balance = round(total_income - total_expense, 2)
    savings = round(expense_transactions.filter(category__name='Savings').aggregate(total=Sum('amount'))['total'] or 0, 2)
    context = {
        'transaction_date': date,
        'end_date': date + timedelta(days=365),
        'form': form,
        'income_transactions': income_transactions,
        'expense_transactions': expense_transactions,
        'total_income': total_income,
        'total_expenses': total_expense,
        'balance': balance,
        'savings': savings,
        'year': year,
        'month': month,
        'day': day,
        'messages': messages
    }
    return render(request, 'transactions.html', context)





@login_required
def create_category(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            category_name = data.get('name').capitalize()

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
    
@login_required
def transaction_list(request):
    # Retrieve all transactions for the logged-in user
    transactions = Transaction.objects.filter(user=request.user)

    # You may want to order the transactions by date or any other criteria
    # transactions = transactions.order_by('-transaction_date')

    context = {
        'transactions': transactions,
    }
    return render(request, 'transaction_list.html', context)

@login_required
def recurring_transactions(request):
    # Query the database to retrieve distinct original transactions
    original_transactions = Transaction.objects.filter(user=request.user, recurring=True, original_transaction__isnull=True).distinct()

    context = {
        'original_transactions': original_transactions
    }

    return render(request, 'recurring_transactions.html', context)