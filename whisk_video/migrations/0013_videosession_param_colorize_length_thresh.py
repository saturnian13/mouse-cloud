# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2018-04-25 23:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('whisk_video', '0012_auto_20171213_2339'),
    ]

    operations = [
        migrations.AddField(
            model_name='videosession',
            name='param_colorize_length_thresh',
            field=models.FloatField(blank=True, null=True),
        ),
    ]