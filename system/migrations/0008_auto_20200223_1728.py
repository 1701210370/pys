# Generated by Django 2.1.4 on 2020-02-23 09:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0007_auto_20200223_1721'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='post_content',
            new_name='content',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='post_senti',
            new_name='senti',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='post_source',
            new_name='source',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='post_time',
            new_name='time',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='post_topic',
            new_name='topic',
        ),
        migrations.RenameField(
            model_name='reply',
            old_name='reply_content',
            new_name='content',
        ),
        migrations.RenameField(
            model_name='reply',
            old_name='reply_senti',
            new_name='senti',
        ),
        migrations.RenameField(
            model_name='reply',
            old_name='reply_source',
            new_name='source',
        ),
        migrations.RenameField(
            model_name='reply',
            old_name='reply_time',
            new_name='time',
        ),
        migrations.RenameField(
            model_name='reply',
            old_name='reply_topic',
            new_name='topic',
        ),
    ]
