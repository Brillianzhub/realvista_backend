# Generated by Django 5.1.2 on 2024-11-22 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_project_project_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='project_reference',
            field=models.CharField(blank=True, max_length=7, null=True, unique=True),
        ),
    ]
