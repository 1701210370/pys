# Generated by Django 2.1.4 on 2020-02-25 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0010_auto_20200224_2105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='topic',
            field=models.CharField(default='1', max_length=20),
        ),
        migrations.AlterField(
            model_name='reply',
            name='topic',
            field=models.CharField(default='1', max_length=20),
        ),
    ]