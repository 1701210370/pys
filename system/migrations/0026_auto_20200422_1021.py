# Generated by Django 2.1.4 on 2020-04-22 02:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0025_info_key_words'),
    ]

    operations = [
        migrations.AlterField(
            model_name='info',
            name='key_words',
            field=models.TextField(null=True),
        ),
    ]