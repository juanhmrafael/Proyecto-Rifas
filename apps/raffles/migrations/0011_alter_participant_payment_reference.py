# Generated by Django 5.1.1 on 2024-10-01 00:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raffles', '0010_alter_participant_payment_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='payment_reference',
            field=models.CharField(max_length=30, unique=True, verbose_name='Referencia del Pago'),
        ),
    ]
