# Generated by Django 4.2.1 on 2023-06-18 00:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0027_alter_products_product_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='image',
            field=models.ImageField(blank=True, upload_to='images'),
        ),
    ]
