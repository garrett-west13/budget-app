from django.db import migrations, models

def populate_original_transaction_id(apps, schema_editor):
    Transaction = apps.get_model('budget', 'Transaction')
    for transaction in Transaction.objects.all():
        transaction.original_transaction_id = None
        transaction.save()

class Migration(migrations.Migration):
    dependencies = [
        ('budget', '0005_delete_goal'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='original_transaction_id',
            field=models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True),
        ),
        migrations.RunPython(populate_original_transaction_id),
    ]