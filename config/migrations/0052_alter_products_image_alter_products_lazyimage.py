# Generated by Django 4.2.1 on 2024-06-29 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0051_alter_products_image_alter_products_lazyimage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='products',
            name='image',
            field=models.ImageField(null=True, upload_to='', verbose_name='images'),
        ),
        migrations.AlterField(
            model_name='products',
            name='lazyImage',
            field=models.ImageField(null=True, upload_to='', verbose_name='images'),
        ),
    ]
