# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import datetime_safe

# Create your models here.


class Task(models.Model):
    content = models.TextField(max_length=500, default='')
    tags = models.TextField(default='')
    priority = models.IntegerField(default=0)
    finished = models.BooleanField(default=False)
    expire_date = models.DateTimeField(default=datetime_safe.datetime.now())
    owner = models.ForeignKey('auth.User', related_name='task', on_delete=models.CASCADE)

