# Generated by Django 4.2.1 on 2023-05-29 21:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0008_remove_item_dummuy'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='size',
            name='image',
        ),
    ]