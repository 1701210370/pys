from django.db import models


# Create your models here.
class post(models.Model):
    post_id = models.CharField(max_length=20, null=False)
    time = models.DateTimeField(auto_now=False)
    content = models.CharField(max_length=240, null=False)
    source = models.IntegerField(null=True, default=0)
    topic = models.CharField(max_length=20, default='1')
    senti = models.IntegerField(null=True)
    # attention = models.CharField(max_length=240, null=True)
    process = models.IntegerField(default=0)
    url = models.CharField(max_length=240, null=True)


class reply(models.Model):
    post_id = models.CharField(max_length=20, null=False)
    reply_id = models.CharField(max_length=20, null=False)
    content = models.CharField(max_length=240, null=False)
    time = models.DateTimeField(auto_now=False)
    source = models.IntegerField(null=True, default=0)
    topic = models.CharField(max_length=20, default='1')
    senti = models.IntegerField(null=True)
    # attention = models.CharField(max_length=240, null=True)
    process = models.IntegerField(default=0)
    url = models.CharField(max_length=240, null=True)


class new_reply(models.Model):
    post_id = models.CharField(max_length=20, null=False)
    reply_id = models.CharField(max_length=20, null=False)
    content = models.CharField(max_length=240, null=False)
    time = models.DateTimeField(auto_now=False)
    source = models.IntegerField(null=True, default=0)
    topic = models.CharField(max_length=20, default='1')
    senti = models.IntegerField(null=True)
    process = models.IntegerField(default=0)
    url = models.CharField(max_length=240, null=True)

class info(models.Model):
    time = models.DateTimeField(auto_now=False)
    senti_value = models.IntegerField(default=0)
    neg_senti_value = models.IntegerField(default=0)
    post_num = models.IntegerField(default=0)
    psy_num = models.IntegerField(default=0)
    study_num = models.IntegerField(default=0)
    career_num = models.IntegerField(default=0)
    love_num = models.IntegerField(default=0)
    others_num = models.IntegerField(default=0)
    key_words = models.TextField(default='')

class high_risk(models.Model):
    post_id = models.CharField(max_length=20, null=False)
    reply_id = models.CharField(max_length=20, null=False)
    content = models.CharField(max_length=240, null=False)
    time = models.DateTimeField(auto_now=False)
    topic = models.CharField(max_length=20, default='1')
    process = models.IntegerField(default=0)
    url = models.CharField(max_length=240, null=True)

class users(models.Model):
    name = models.CharField(max_length=20, null=False)
    password = models.CharField(max_length=20, null=False)
    email = models.CharField(max_length=240, null=False)


class hole(models.Model):
    post_id = models.CharField(max_length=20, null=False)
    time = models.DateTimeField(auto_now=False)
    content = models.CharField(max_length=240, null=False)
    source = models.IntegerField(null=True, default=0)
    topic = models.CharField(max_length=20, default='1')
    senti = models.IntegerField(null=True)
    # attention = models.CharField(max_length=240, null=True)
    process = models.IntegerField(default=0)
    # url = models.CharField(max_length=240, null=True)
    page = models.IntegerField(default=0)