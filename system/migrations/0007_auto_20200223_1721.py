# Generated by Django 2.1.4 on 2020-02-23 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0006_auto_20200223_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_topic',
            field=models.CharField(default=None, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='reply',
            name='reply_topic',
            field=models.CharField(default=None, max_length=20, null=True),
        ),
    ]