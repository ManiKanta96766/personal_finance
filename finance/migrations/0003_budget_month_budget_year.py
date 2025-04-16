# Generated by Django 5.2 on 2025-04-16 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_rename_limit_budget_amount_transaction_receipt_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='budget',
            name='month',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='budget',
            name='year',
            field=models.IntegerField(default=2025),
            preserve_default=False,
        ),
    ]
