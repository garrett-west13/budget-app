# Generated by Django 5.0.4 on 2024-05-03 19:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0002_transaction_end_date_transaction_frequency_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='date',
        ),
    ]
