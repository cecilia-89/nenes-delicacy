# Generated by Django 4.2.1 on 2024-07-18 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0059_alter_producttype_bannerimage_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]
