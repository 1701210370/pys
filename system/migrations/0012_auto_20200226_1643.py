# Generated by Django 2.1.4 on 2020-02-26 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0011_auto_20200225_1256'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='attention',
            field=models.CharField(max_length=240, null=True),
        ),
        migrations.AddField(
            model_name='reply',
            name='attention',
            field=models.CharField(max_length=240, null=True),
        ),
    ]
