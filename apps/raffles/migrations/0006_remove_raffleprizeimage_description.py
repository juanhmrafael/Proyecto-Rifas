# Generated by Django 5.1.1 on 2024-09-27 15:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('raffles', '0005_alter_participant_payment_receipt_raffleprizeimage'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='raffleprizeimage',
            name='description',
        ),
    ]
