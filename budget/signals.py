from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Transaction
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from django.db.models import Q




@receiver(post_save, sender=User)
def create_savings_category(sender, instance, created, **kwargs):
    """
    Automatically creates a 'Savings' category for every new user.
    """
    if created:
        Category.objects.create(user=instance, name='Savings')


@receiver(pre_delete, sender=Transaction)
def handle_delete_recurring_transaction(sender, instance, **kwargs):
    """
    Delete all future occurrences of the recurring transaction when it is deleted.
    """
    if instance.recurring:
        with transaction.atomic():
            # Disconnect the signal temporarily to avoid recursion
            pre_delete.disconnect(handle_delete_recurring_transaction, sender=Transaction)
            
            try:
                Transaction.objects.filter(
                    Q(user=instance.user) &
                    Q(description=instance.description) &
                    Q(transaction_date__gte=timezone.now().date()) &
                    Q(frequency=instance.frequency)
                ).delete()
            finally:
                # Reconnect the signal after deletion
                pre_delete.connect(handle_delete_recurring_transaction, sender=Transaction)
                

@receiver(pre_save, sender=Transaction)
def handle_update_recurring_transaction(sender, instance, **kwargs):
    """
    Update all future occurrences of the recurring transaction when it is updated.
    """
    if instance.recurring and instance.pk:
        original_transaction = Transaction.objects.get(pk=instance.pk)
        if original_transaction.transaction_date != instance.transaction_date:
            Transaction.objects.filter(
                Q(user=instance.user) &
                Q(description=instance.description) &
                Q(transaction_date__gte=timezone.now().date()) &
                Q(frequency=instance.frequency)
            ).update(
                transaction_date=instance.transaction_date
            )

@receiver(post_save, sender=Transaction)
def handle_recurring_transaction(sender, instance, created, **kwargs):
    """
    Automatically creates or updates recurring transactions based on the original transaction.
    """
    if instance.recurring:
        with transaction.atomic():
            # Check if the original transaction is being updated
            if not created:
                # Update existing recurring transactions
                Transaction.objects.filter(original_transaction=instance).update(
                    amount=instance.amount,
                    description=instance.description,
                    category=instance.category,
                    is_income=instance.is_income,
                    transaction_date=instance.transaction_date,
                    frequency=instance.frequency,
                    start_date=instance.start_date,
                    end_date=instance.end_date
                )
            else:
                # Delete existing recurring transactions if a new recurring transaction is created
                Transaction.objects.filter(original_transaction=instance).delete()
                create_or_update_recurring_transactions(instance)



def create_or_update_recurring_transactions(recurring_transaction):
    if recurring_transaction.recurring:
        current_date = recurring_transaction.transaction_date
        end_date = recurring_transaction.end_date
        existing_transactions = Transaction.objects.filter(
            Q(user=recurring_transaction.user) &
            Q(description=recurring_transaction.description) &
            Q(transaction_date__gte=current_date) & 
            Q(transaction_date__lte=end_date) &
            Q(frequency=recurring_transaction.frequency)
        )

        existing_dates = set(existing_transactions.values_list('transaction_date', flat=True))

        new_transactions = []
        while current_date < end_date:
            if current_date not in existing_dates:
                new_transaction = Transaction(
                    user=recurring_transaction.user,
                    amount=recurring_transaction.amount,
                    description=recurring_transaction.description,
                    category=recurring_transaction.category,
                    is_income=recurring_transaction.is_income,
                    transaction_date=current_date,
                    recurring=True,  
                    frequency=recurring_transaction.frequency,
                    start_date=recurring_transaction.start_date,
                    end_date=recurring_transaction.end_date,
                    original_transaction=recurring_transaction 
                )
                new_transactions.append(new_transaction)
                existing_dates.add(current_date)

            # Increment the current date based on the frequency
            if recurring_transaction.frequency == 'monthly':
                current_date += relativedelta(months=1)
            elif recurring_transaction.frequency == 'weekly':
                current_date += relativedelta(weeks=1)
            elif recurring_transaction.frequency == 'biweekly':
                current_date += relativedelta(weeks=2)
            elif recurring_transaction.frequency == 'yearly':
                current_date += relativedelta(years=1)

        # Bulk create the new transactions outside of the loop
        with transaction.atomic():
            new_transactions = Transaction.objects.bulk_create(new_transactions)
        
        # Set the recurring field of the last transaction to False if its date matches the end date
        if new_transactions and new_transactions[-1].transaction_date >= end_date:
            last_transaction = new_transactions[-1]
            last_transaction.recurring = False
            # Use update() to avoid triggering post_save signal
            Transaction.objects.filter(pk=last_transaction.pk).update(recurring=False)
