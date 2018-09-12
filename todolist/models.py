# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import datetime_safe
import time

current_milli_time = lambda: int(round(time.time() * 1000))


# Create your models here.


class Task(models.Model):
    content = models.TextField(max_length=500, default='')
    tags = models.TextField(default='')
    priority = models.IntegerField(default=0)
    finished = models.BooleanField(default=False)
    expire_date = models.CharField(max_length=15, default=current_milli_time())
    owner = models.ForeignKey('auth.User', related_name='task', on_delete=models.CASCADE)

