# Generated by Django 5.1.1 on 2024-10-01 16:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raffles', '0012_alter_participant_full_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='payment_reference',
            field=models.IntegerField(unique=True, verbose_name='Referencia del Pago'),
        ),
    ]
