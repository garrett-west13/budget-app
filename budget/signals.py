from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Transaction
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.db import transaction
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
    Update future occurrences of the recurring transaction when it is updated.
    """
    if instance.recurring and instance.pk:
        try:
            original_transaction = Transaction.objects.get(pk=instance.pk)
            if original_transaction.transaction_date != instance.transaction_date:
                # Update future occurrences of the recurring transaction
                update_recurring_transactions(instance)
        except Transaction.DoesNotExist:
            pass


@receiver(post_save, sender=Transaction)
def handle_recurring_transaction(sender, instance, created, **kwargs):
    """
    Automatically updates recurring transactions based on the original transaction.
    """
    if instance.recurring and not created:
        with transaction.atomic():
            try:
                # Update future occurrences of the recurring transaction
                update_recurring_transactions(instance)
            except Exception as e:
                # Handle exceptions gracefully
                print(f"An error occurred while updating recurring transactions: {e}")


def update_recurring_transactions(transaction):
    """
    Updates future occurrences of the recurring transaction.
    """
    if transaction.recurring:
        current_date = transaction.transaction_date
        end_date = transaction.end_date

        # Update future occurrences of the recurring transaction
        Transaction.objects.filter(
            Q(user=transaction.user) &
            Q(description=transaction.description) &
            Q(transaction_date__gte=current_date) &
            Q(frequency=transaction.frequency)
        ).exclude(pk=transaction.pk).update(
            transaction_date=transaction.transaction_date
        )
