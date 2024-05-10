from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Transaction
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from django.db.models import Q, F


# Function to create a 'Savings' category for every new user
@receiver(post_save, sender=User)
def create_savings_category(sender, instance, created, **kwargs):
    """
    Automatically creates a 'Savings' category for every new user.
    """
    if created:
        Category.objects.create(user=instance, name='Savings')


@receiver(pre_delete, sender=Transaction)
def handle_delete_recurring_transaction(sender, instance, is_update=False, **kwargs):
    """
    Delete future occurrences of the recurring transaction when it is deleted.
    """
    if instance.recurring and not is_update:
        with transaction.atomic():
            # Disconnect the signal temporarily to avoid recursion
            pre_delete.disconnect(handle_delete_recurring_transaction, sender=Transaction)
            try:
                # Delete subsequent occurrences
                Transaction.objects.filter(
                    Q(user=instance.user) &
                    Q(description=instance.description) &
                    Q(transaction_date__gt=timezone.now().date()) &
                    Q(transaction_date__lte=instance.end_date)
                ).delete()
            finally:
                # Reconnect the signal after deletion
                pre_delete.connect(handle_delete_recurring_transaction, sender=Transaction)
    elif instance.recurring and is_update:
        with transaction.atomic():
            # Disconnect the signal temporarily to avoid recursion
            pre_delete.disconnect(handle_delete_recurring_transaction, sender=Transaction)
            try:
                # Delete subsequent occurrences, excluding the transaction being updated
                Transaction.objects.filter(
                    Q(user=instance.user) &
                    Q(description=instance.description) &
                    Q(transaction_date__gt=timezone.now().date()) &
                    ~Q(id=instance.id)  # Exclude the transaction being updated
                ).delete()
            finally:
                # Reconnect the signal after deletion
                pre_delete.connect(handle_delete_recurring_transaction, sender=Transaction)
    else:
        pass



@receiver(post_save, sender=Transaction)
def handle_recurring_transaction(sender, instance, created, **kwargs):
    """
    Automatically creates or updates recurring transactions based on the original transaction.
    """
    if instance.recurring:
        with transaction.atomic():
            if created:
                # If the transaction is newly created, delete old recurring transactions
                create_or_update_recurring_transactions(instance)
            else:
                # If the transaction is updated, always recreate future occurrences
                handle_delete_recurring_transaction(sender=sender, instance=instance, is_update=True, **kwargs)
                create_or_update_recurring_transactions(instance)


def create_or_update_recurring_transactions(recurring_transaction):
    if recurring_transaction.recurring and recurring_transaction.start_date is not None:
        current_date = recurring_transaction.start_date.date()
    else:
        current_date = recurring_transaction.transaction_date


    end_date = recurring_transaction.end_date
    frequency = recurring_transaction.frequency

    existing_transactions = Transaction.objects.filter(
        Q(user=recurring_transaction.user) &
        Q(description=recurring_transaction.description) &
        Q(transaction_date__gte=current_date) &
        Q(transaction_date__lte=end_date) &
        Q(frequency=frequency)
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
                frequency=frequency,
                start_date=recurring_transaction.start_date,
                end_date=recurring_transaction.end_date,
                original_transaction=recurring_transaction
            )
            new_transactions.append(new_transaction)
            existing_dates.add(current_date)

        # Increment the current date based on the frequency
        if frequency == 'monthly':
            current_date += relativedelta(months=1)
        elif frequency == 'weekly':
            current_date += relativedelta(weeks=1)
        elif frequency == 'biweekly':
            current_date += relativedelta(weeks=2)
        elif frequency == 'yearly':
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


