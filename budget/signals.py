from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Transaction
from dateutil.relativedelta import relativedelta
from django.db.models.signals import pre_delete, pre_save
from django.utils import timezone
from django.db import transaction
from datetime import datetime




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
            user=instance.user,
            description=instance.description,
            transaction_date__gte=timezone.now().date()
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
                user=instance.user,
                description=instance.description,
                transaction_date__gte=timezone.now().date()
            ).update(
                transaction_date=instance.transaction_date
            )

@receiver(post_save, sender=Transaction)
def handle_recurring_transaction(sender, instance, created, **kwargs):
    """
    Automatically creates recurring transactions based on the original transaction.
    """
    if created and instance.recurring:
        with transaction.atomic():
            create_recurring_transactions(instance)

def create_recurring_transactions(transaction):
    if transaction.recurring:
        current_date = transaction.transaction_date.date()  # Convert to datetime.date
        while current_date <= transaction.end_date:
            # Check if a transaction for the same date and description already exists
            if not Transaction.objects.filter(user=transaction.user, description=transaction.description, transaction_date=current_date).exists():
                # Create a new transaction based on the original transaction
                new_transaction = Transaction.objects.create(
                    user=transaction.user,
                    amount=transaction.amount,
                    description=transaction.description,
                    category=transaction.category,
                    is_income=transaction.is_income,
                    transaction_date=current_date
                )
            # Increment the current date based on the frequency
            if transaction.frequency == 'monthly':
                current_date += relativedelta(months=1)
            elif transaction.frequency == 'weekly':
                current_date += relativedelta(weeks=1)
            elif transaction.frequency == 'biweekly':
                current_date += relativedelta(weeks=2)
            elif transaction.frequency == 'yearly':
                current_date += relativedelta(years=1)