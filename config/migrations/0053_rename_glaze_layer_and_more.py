# Generated by Django 4.2.1 on 2024-07-12 01:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0052_alter_products_image_alter_products_lazyimage'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Glaze',
            new_name='Layer',
        ),
        migrations.AlterField(
            model_name='shippingaddress',
            name='deliveryDate',
            field=models.DateField(blank=True, null=True),
        ),
    ]
