import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, TransactionForm
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from .calendar import Calendar
from datetime import datetime
from .models import Transaction, Category
from django.http import JsonResponse, Http404, HttpResponse
from django.db.models import Sum, F
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from django.urls import reverse


@login_required
def store_selected_month_year(request):
    if request.method == 'POST':
        # Retrieve the JSON data from the request body
        data = json.loads(request.body)
        selected_month = data.get('selectedMonth')
        selected_year = data.get('selectedYear')

        # Store the selected month and year in the Django session
        request.session['selectedMonth'] = selected_month
        request.session['selectedYear'] = selected_year


        # Return a JSON response indicating success
        return JsonResponse({'message': 'Selected month and year stored successfully'})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)





def index(request):

    return render(request, 'index.html')

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

            if transaction.recurring:
                end_date = form.cleaned_data.get('end_date')
                frequency = form.cleaned_data.get('frequency')
                if not end_date or not frequency:
                    messages.error(request, 'Please provide both end date and frequency for recurring transactions.')
                    return render(request, 'transactions.html', {'form': form})

                transaction.frequency = frequency
                transaction.start_date = date
                transaction.save()

                messages.success(request, 'Recurring transaction added successfully.')
                return redirect('recurring_transactions')
            else:
                transaction.end_date = None
                transaction.save()
                messages.success(request, 'Transaction added successfully.')
                return redirect('add_transaction', year=year, month=month, day=day)

    else:
        form = TransactionForm(request.user, initial={'transaction_date': date})

    transactions = Transaction.objects.filter(user=request.user, transaction_date=date)
    income_transactions = transactions.filter(is_income=True)
    expense_transactions = transactions.filter(is_income=False)

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
def recurring_transactions(request):
    # Query the database to retrieve distinct original transactions
    original_transactions = Transaction.objects.filter(user=request.user, recurring=True, original_transaction__isnull=True).distinct()

    context = {
        'original_transactions': original_transactions
    }

    return render(request, 'recurring_transactions.html', context)

@login_required
def recurring_transaction_detail(request, pk):
    transactions = Transaction.objects.filter(user=request.user, original_transaction_id=pk)

    context = {
        'transactions': transactions
    }

    return render(request, 'recurring_transaction_detail.html', context)

@login_required
def calculate_totals(request):

    # Retrieve selected month and year from session
    stored_year = request.session.get('selectedYear')
    stored_month = request.session.get('selectedMonth')

    if stored_month is not None and stored_year is not None:
        current_month = int(stored_month + 1)
        current_year = int(stored_year)
    else:
        # Set default values for current month and year
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month

    # Calculate total expenses for the month
    total_expenses = round(Transaction.objects.filter(
        transaction_date__year=current_year,
        transaction_date__month=current_month,
        is_income=False
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0, 2)

    # Calculate total income for the month
    total_income = round(Transaction.objects.filter(
        transaction_date__year=current_year,
        transaction_date__month=current_month,
        is_income=True
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0, 2)

    # Calculate total balance for the month
    total_balance = round(float(total_income) - float(total_expenses), 2)

    # Calculate total savings for the month (if applicable)
    total_savings = round(Transaction.objects.filter(
        transaction_date__year=current_year,
        transaction_date__month=current_month,
        is_income=False,
        category__name='Savings'
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0, 2)

    # Return JSON data containing the totals
    data = {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'total_balance': total_balance,
        'total_savings': total_savings
    }
    return JsonResponse(data)

@login_required
def transaction_list(request):
    # Retrieve all transactions for the logged-in user
    transactions = Transaction.objects.filter(user=request.user, recurring=False, original_transaction__isnull=True).order_by('-transaction_date')

    # Filter out the original instances of recurring transactions
    original_transactions = Transaction.objects.filter(user=request.user, recurring=True, original_transaction__isnull=True).distinct().order_by('-transaction_date')

    context = {
        'transactions': transactions,
        'recurring_transactions': original_transactions,
    }
    return render(request, 'transaction_list.html', context)



@login_required
def update_transaction(request, pk):
    transaction = get_object_or_404(Transaction, id=pk, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.user, request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(request.user, instance=transaction)

    # Pass the 'transaction' object to the template context
    return render(request, 'transaction_update.html', {'form': form, 'transaction': transaction})




@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, id=pk)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully.')
        return redirect('transaction_list')

    return redirect('transaction_list')
