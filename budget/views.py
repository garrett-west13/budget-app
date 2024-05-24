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
from django.db.models import Sum, Count, Q
from datetime import timedelta


@login_required
def store_selected_month_year(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        selected_month = data.get('selectedMonth')
        selected_year = data.get('selectedYear')

        request.session['selectedMonth'] = selected_month
        request.session['selectedYear'] = selected_year

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

                messages.error(request, 'This username is already taken. Please choose a different one.')
            else:
                form.save()
                messages.success(request, f'Account created for {username}. You can now log in.')
                return redirect('login')
        else:
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
                return redirect('add_transaction', year=year, month=month, day=day)
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
    }
    return render(request, 'transactions.html', context)

@login_required
def create_category(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category_name = data.get('name').capitalize()

            if not category_name:
                raise ValueError('Category name is missing or empty')

            category = Category.objects.create(name=category_name, user=request.user)

            return JsonResponse({'id': category.id, 'name': category.name})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)  

def calendar(request, year, month):
    calendar = Calendar()
    calendar_html = calendar.formatmonth(year, month)
    return HttpResponse(calendar_html)

@login_required
def recurring_transaction_detail(request, pk):
    try:
        # Attempt to retrieve the original transaction
        original_transaction = Transaction.objects.get(id=pk, user=request.user)

        # Check if the provided pk corresponds to the original transaction
        if original_transaction.original_transaction is not None:
            # If the pk is not the original transaction, raise a 404 error
            raise Http404("This transaction is not the original one.")

        # Retrieve all related transactions based on the original transaction
        transactions = Transaction.objects.filter(user=request.user, related_transaction=original_transaction)

        # If no related transactions are found, inform the user
        if not transactions.exists():
            messages.info(request, 'No related recurring transactions found.')

        context = {
            'transactions': transactions,
            'original_transaction': original_transaction
        }

        return render(request, 'recurring_transaction_detail.html', context)

    except Transaction.DoesNotExist:
        raise Http404("Transaction not found.")




@login_required
def calculate_totals(request):

    stored_year = request.session.get('selectedYear')
    stored_month = request.session.get('selectedMonth')

    if stored_month is not None and stored_year is not None:
        current_month = int(stored_month + 1)
        current_year = int(stored_year)
    else:

        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month


    total_expenses = round(Transaction.objects.filter(
        transaction_date__year=current_year,
        transaction_date__month=current_month,
        is_income=False
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0, 2)

    total_income = round(Transaction.objects.filter(
        transaction_date__year=current_year,
        transaction_date__month=current_month,
        is_income=True
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0, 2)

    total_balance = round(float(total_income) - float(total_expenses), 2)

    total_savings = round(Transaction.objects.filter(
        transaction_date__year=current_year,
        transaction_date__month=current_month,
        is_income=False,
        category__name='Savings'
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0, 2)

    data = {
        'total_expenses': total_expenses,
        'total_income': total_income,
        'total_balance': total_balance,
        'total_savings': total_savings
    }
    return JsonResponse(data)

@login_required
def transaction_list(request, year=None, month=None):
    try:
        year = int(year) if year is not None else None
        month = int(month) if month is not None else None
    except ValueError:
        raise Http404("Invalid date")

    if year is not None and month is not None:
        try:
            date = datetime(year=year, month=month, day=1)
        except ValueError:
            raise Http404("Invalid date")
    else:
        date = datetime.now()
        year = date.year
        month = date.month

    transactions = Transaction.objects.filter(user=request.user, recurring=False, original_transaction__isnull=True, transaction_date__year=year, transaction_date__month=month)

    recurring_transactions = Transaction.objects.filter(user=request.user, recurring=True, transaction_date__year=year, transaction_date__month=month)

    context = {
        'transactions': transactions,
        'recurring_transactions': recurring_transactions,
        'date': date,
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
            return redirect('transaction_list', year=transaction.transaction_date.year, month=transaction.transaction_date.month)

    else:
        form = TransactionForm(request.user, instance=transaction)

    return render(request, 'transaction_update.html', {'form': form, 'transaction': transaction})

@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, id=pk, user=request.user)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully.')
        return redirect('transaction_list', year=transaction.transaction_date.year, month=transaction.transaction_date.month)

    return redirect('transaction_list', year=transaction.transaction_date.year, month=transaction.transaction_date.month)


@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).annotate(transaction_count=Count('transaction')).order_by('name')
    return render(request, 'category_list.html', {'categories': categories})

@login_required
def category_detail(request, pk):
    category = get_object_or_404(Category, id=pk, user=request.user)
    transactions = Transaction.objects.filter(user=request.user, category=category)
    
    context = {
        'category': category,
        'transactions': transactions
    }
    
    return render(request, 'category_detail.html', context)

@login_required
def delete_category(request, pk):

    category = get_object_or_404(Category, id=pk, user=request.user)
    category.delete()
    messages.success(request, 'Category deleted successfully.')
    return redirect('category_list')

@login_required
def yearly_summary(request, year=None):
    if year is None:
        year = datetime.now().year

    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__year=year
    )

    total_income = round(transactions.filter(is_income=True).aggregate(total=Sum('amount'))['total'] or 0, 2)
    total_expenses = round(transactions.filter(is_income=False).aggregate(total=Sum('amount'))['total'] or 0, 2)

    balance = round(total_income - total_expenses, 2)

    total_savings = round(transactions.filter(category__name='Savings', is_income=False).aggregate(total=Sum('amount'))['total'] or 0, 2)

    monthly_summaries = {}
    for month in range(1, 13):
        month_name = datetime.strptime(str(month), "%m").strftime("%B")
        month_transactions = transactions.filter(transaction_date__month=month)

        month_total_income = round(month_transactions.filter(is_income=True).aggregate(total=Sum('amount'))['total'] or 0, 2)
        month_total_expenses = round(month_transactions.filter(is_income=False).aggregate(total=Sum('amount'))['total'] or 0, 2)

        month_balance = round(month_total_income - month_total_expenses, 2)

        month_savings = round(month_transactions.filter(category__name='Savings', is_income=False).aggregate(total=Sum('amount'))['total'] or 0, 2)

        monthly_summaries[month_name] = {
            'total_income': month_total_income,
            'total_expenses': month_total_expenses,
            'balance': month_balance,
            'total_savings': month_savings,
        }

    yearly_summary_data = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'total_savings': total_savings,
        'monthly_summaries': monthly_summaries,
        'selected_year': year
    }

    return render(request, 'yearly_summary.html', {'yearly_summary': yearly_summary_data})

@login_required
def update_all_transactions(request, pk):
    try:
        # Retrieve the transaction
        original_transaction = get_object_or_404(Transaction, id=pk, user=request.user)

        if request.method == 'POST':
            # Get the form data for the original transaction
            form = TransactionForm(request.user, request.POST, instance=original_transaction)
            if form.is_valid():
                # Save the original transaction
                form.save()

                # Retrieve all subsequent recurring transactions
                transactions = Transaction.objects.filter(
                    user=request.user, 
                    original_transaction=original_transaction
                )

                # Update fields
                for t in transactions:
                    t.amount = original_transaction.amount
                    t.description = original_transaction.description
                    t.category = original_transaction.category
                    t.is_income = original_transaction.is_income
                    t.end_date = original_transaction.end_date
                    t.start_date = original_transaction.start_date
                    t.frequency = original_transaction.frequency
                    t.recurring = original_transaction.recurring

                # Bulk update transactions
                Transaction.objects.bulk_update(transactions, [
                    'amount', 'description', 'category', 'is_income', 'end_date', 
                    'start_date', 'frequency', 'recurring'
                ])

                messages.success(request, 'All transactions updated successfully.')
                return redirect('recurring_transaction_detail', pk=original_transaction.id)
        else:
            form = TransactionForm(request.user, instance=original_transaction)

        return render(request, 'update_all_transactions.html', {'form': form, 'transaction': original_transaction})

    except Transaction.DoesNotExist:
        raise Http404("Transaction not found.")


@login_required
def delete_all_transactions(request, pk):
    if request.method == 'POST':
        try:
            # Retrieve the transaction
            original_transaction = Transaction.objects.get(user=request.user, id=pk)

            transactions = Transaction.objects.filter(
                user=request.user,
                original_transaction=original_transaction
            )

            # Delete all related recurring transactions
            transactions.delete()
            original_transaction.delete()

            messages.success(request, 'All transactions deleted successfully.')
            return redirect('transaction_list', year=original_transaction.transaction_date.year, month=original_transaction.transaction_date.month)
        
        except Transaction.DoesNotExist:
            messages.error(request, 'Transaction not found.')
            return redirect('transaction_list', year=original_transaction.transaction_date.year, month=original_transaction.transaction_date.month)

