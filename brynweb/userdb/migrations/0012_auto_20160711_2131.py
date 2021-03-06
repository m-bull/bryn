# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-11 21:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userdb', '0011_auto_20160711_2109'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('description', models.CharField(max_length=40)),
            ],
        ),
        migrations.AddField(
            model_name='team',
            name='default_region',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='userdb.Region'),
            preserve_default=False,
        ),
    ]
