# Generated by Django 5.1.2 on 2024-11-18 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('not_paid', 'Not Paid'), ('paid', 'Paid'), ('payment_confirm', 'Payment Confirmed')], default='not_paid', max_length=20),
        ),
    ]