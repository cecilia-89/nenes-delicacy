# Generated by Django 4.2.1 on 2023-09-18 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('config', '0040_shipment'),
    ]

    operations = [
        migrations.CreateModel(
            name='States',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(max_length=100)),
                ('lga', models.JSONField(null=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Shipment',
        ),
    ]
