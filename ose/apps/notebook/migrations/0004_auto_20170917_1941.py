# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-18 00:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notebook', '0003_auto_20170910_2103'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ('-day', '-updated'), 'verbose_name': 'Log Entry', 'verbose_name_plural': 'Log Entries'},
        ),
    ]
