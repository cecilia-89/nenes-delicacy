# Generated by Django 4.2.1 on 2023-08-30 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0034_remove_cart_user_alter_cart_session_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='cart',
        ),
        migrations.AddField(
            model_name='cartitem',
            name='cart',
            field=models.ManyToManyField(blank=True, null=True, to='config.cart'),
        ),
    ]
