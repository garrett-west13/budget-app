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
        Transaction.objects.filter(
            Q(user=instance.user) &
            Q(description=instance.description) &
            Q(transaction_date__gte=timezone.now().date()) &
            Q(frequency=instance.frequency)
        ).delete()

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
            create_or_update_recurring_transactions(instance)

def create_or_update_recurring_transactions(transaction):
    if transaction.recurring:
        current_date = transaction.start_date
        end_date = transaction.end_date
        existing_transactions = Transaction.objects.filter(
            Q(user=transaction.user) &
            Q(description=transaction.description) &
            Q(transaction_date__range=[current_date, end_date]) &
            Q(frequency=transaction.frequency)
        )

        existing_dates = set(existing_transactions.values_list('transaction_date', flat=True))

        while current_date <= end_date:
            if current_date not in existing_dates:
                # Create a new transaction based on the original transaction
                new_transaction = Transaction.objects.create(
                    user=transaction.user,
                    amount=transaction.amount,
                    description=transaction.description,
                    category=transaction.category,
                    is_income=transaction.is_income,
                    transaction_date=current_date,
                    recurring=transaction.recurring,
                    frequency=transaction.frequency,
                    start_date=transaction.start_date,
                    end_date=transaction.end_date
                )
                existing_dates.add(current_date)

            # Increment the current date based on the frequency
            if transaction.frequency == 'monthly':
                current_date += relativedelta(months=1)
            elif transaction.frequency == 'weekly':
                current_date += relativedelta(weeks=1)
            elif transaction.frequency == 'biweekly':
                current_date += relativedelta(weeks=2)
            elif transaction.frequency == 'yearly':
                current_date += relativedelta(years=1)