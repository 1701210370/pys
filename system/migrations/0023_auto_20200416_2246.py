# Generated by Django 2.1.4 on 2020-04-16 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0022_high_risk'),
    ]

    operations = [
        migrations.AddField(
            model_name='info',
            name='career_num',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='info',
            name='love_num',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='info',
            name='others_num',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='info',
            name='psy_num',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='info',
            name='study_num',
            field=models.IntegerField(default=0),
        ),
    ]
