# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2017-01-24 04:41


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_metadata', '0042_auto_20170119_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='courserun',
            name='course_overridden',
            field=models.BooleanField(default=False, help_text='Indicates whether the course relation has been manually overridden.'),
        ),
    ]
