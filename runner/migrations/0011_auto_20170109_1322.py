# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-01-09 18:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0010_auto_20170109_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='grandsession',
            name='name',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='grandsession',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]