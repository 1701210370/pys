# Generated by Django 2.1.4 on 2020-02-24 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0009_auto_20200224_2104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reply',
            name='time',
            field=models.DateTimeField(),
        ),
    ]