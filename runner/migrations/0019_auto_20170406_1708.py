# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2017-04-06 21:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('runner', '0018_mouse_task_reaction_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mouse',
            name='task_reaction_time',
            field=models.CharField(default='', max_length=10),
        ),
    ]
