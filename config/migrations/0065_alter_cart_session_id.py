# Generated by Django 5.1 on 2024-08-10 05:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0064_alter_productvariation_filling_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cart',
            name='session_id',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
