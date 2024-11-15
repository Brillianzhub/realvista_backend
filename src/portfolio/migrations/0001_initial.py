# Generated by Django 5.1.2 on 2024-11-04 15:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(max_length=255)),
                ('property_type', models.CharField(choices=[('land', 'Land'), ('building', 'Building'), ('commercial', 'Commercial Property'), ('residential', 'Residential Property')], max_length=50)),
                ('initial_cost', models.DecimalField(decimal_places=2, max_digits=15)),
                ('current_value', models.DecimalField(decimal_places=2, max_digits=15)),
                ('added_on', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Coordinate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('property', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coordinates', to='portfolio.property')),
            ],
        ),
    ]
