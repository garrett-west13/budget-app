from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Category, Transaction
from dateutil.relativedelta import relativedelta
from django.db import transaction


# Function to create a 'Savings' category for every new user
@receiver(post_save, sender=User)
def create_savings_category(sender, instance, created, **kwargs):
    """
    Automatically creates a 'Savings' category for every new user.
    """
    if created:
        Category.objects.create(user=instance, name='Savings')


@receiver(post_save, sender=Transaction)
def handle_recurring_transaction(sender, instance, created, **kwargs):
    """
    Automatically creates subsequent recurring transactions when the original transaction is created.
    """
    if instance.recurring and created:
        create_recurring_transactions(instance)

def create_recurring_transactions(recurring_transaction):
    """
    Create subsequent recurring transactions based on the original transaction.
    """
    if recurring_transaction.start_date is not None:
        current_date = recurring_transaction.start_date.date()
    else:
        current_date = recurring_transaction.transaction_date

    end_date = recurring_transaction.end_date
    frequency = recurring_transaction.frequency

    new_transactions = []
    while current_date < end_date:
        if current_date != recurring_transaction.transaction_date:
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
                original_transaction=recurring_transaction,
                related_transaction=recurring_transaction 
            )
            new_transactions.append(new_transaction)

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
        Transaction.objects.bulk_create(new_transactions)

    # Set the recurring field of the last transaction to False if its date matches the end date
    if new_transactions and new_transactions[-1].transaction_date >= end_date:
        last_transaction = new_transactions[-1]
        last_transaction.recurring = False
        last_transaction.save(update_fields=['recurring'])


