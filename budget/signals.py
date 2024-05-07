from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Transaction
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from django.db.models import Q, F




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
        # Disconnect the pre_delete signal temporarily to avoid recursion
        pre_delete.disconnect(handle_delete_recurring_transaction, sender=Transaction)

        with transaction.atomic():
            # Delete future occurrences
            Transaction._base_manager.filter(
                Q(user=instance.user) &
                Q(description=instance.description) &
                Q(transaction_date__gte=instance.transaction_date) &
                Q(frequency=instance.frequency)
            ).exclude(pk=instance.pk).delete()

        # Reconnect the pre_delete signal
        pre_delete.connect(handle_delete_recurring_transaction, sender=Transaction)



@receiver(pre_save, sender=Transaction)
def handle_update_recurring_transaction(sender, instance, **kwargs):
    """
    Update all future occurrences of the recurring transaction when it is updated.
    """
    if instance.recurring and instance.pk:
        try:
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
        except Transaction.DoesNotExist:
            pass  # Original transaction not found, do nothing or handle gracefully



@receiver(post_save, sender=Transaction)
def handle_recurring_transaction(sender, instance, created, **kwargs):
    """
    Automatically creates or updates recurring transactions based on the original transaction.
    """
    if instance.recurring:
        with transaction.atomic():
            create_or_update_recurring_transactions(instance)



def create_or_update_recurring_transactions(transaction):
    if transaction.recurring:
        current_date = transaction.transaction_date
        end_date = transaction.end_date
        existing_transactions = Transaction.objects.filter(
            Q(user=transaction.user) &
            Q(description=transaction.description) &
            Q(transaction_date__gte=current_date) & 
            Q(transaction_date__lte=end_date) &
            Q(frequency=transaction.frequency)
        )

        existing_dates = set(existing_transactions.values_list('transaction_date', flat=True))

        new_transactions = []
        # Skip creating the original transaction again
        if current_date not in existing_dates:
            new_transaction = Transaction(
                user=transaction.user,
                amount=transaction.amount,
                description=transaction.description,
                category=transaction.category,
                is_income=transaction.is_income,
                transaction_date=current_date,
                recurring=True,  
                frequency=transaction.frequency,
                start_date=transaction.start_date,
                end_date=transaction.end_date,
                original_transaction=transaction.original_transaction or transaction  # Set the original transaction
            )
            new_transactions.append(new_transaction)
            existing_dates.add(current_date)

        while current_date < end_date:
            # Increment the current date based on the frequency
            if transaction.frequency == 'monthly':
                current_date += relativedelta(months=1)
            elif transaction.frequency == 'weekly':
                current_date += relativedelta(weeks=1)
            elif transaction.frequency == 'biweekly':
                current_date += relativedelta(weeks=2)
            elif transaction.frequency == 'yearly':
                current_date += relativedelta(years=1)
            
            # Skip existing dates
            if current_date in existing_dates:
                continue
            
            new_transaction = Transaction(
                user=transaction.user,
                amount=transaction.amount,
                description=transaction.description,
                category=transaction.category,
                is_income=transaction.is_income,
                transaction_date=current_date,
                recurring=True,  
                frequency=transaction.frequency,
                start_date=transaction.start_date,
                end_date=transaction.end_date,
                original_transaction=transaction.original_transaction or transaction  # Set the original transaction
            )
            new_transactions.append(new_transaction)
            existing_dates.add(current_date)

        # Bulk create the new transactions outside of the loop
        new_transactions = Transaction.objects.bulk_create(new_transactions)

        # Get the last transaction from the list
        if new_transactions:
            last_transaction = new_transactions[-1]

            # Set the recurring field of the last transaction to False if its date matches the end date
            if last_transaction.transaction_date >= end_date:
                last_transaction.recurring = False
                last_transaction.save(update_fields=['recurring'])
