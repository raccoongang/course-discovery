# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-03 19:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publisher', '0073_drupalloaderconfig_load_unpublished_course_runs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='courserun',
            name='preview_url',
        ),
        migrations.RemoveField(
            model_name='historicalcourserun',
            name='preview_url',
        ),
    ]