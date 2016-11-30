# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-11-29 13:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('WechatApi', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=64)),
                ('birthday', models.DateField(null=True)),
                ('sex', models.NullBooleanField()),
                ('intro', models.CharField(default='', max_length=1024)),
                ('avatar', models.CharField(max_length=256, null=True)),
                ('phone', models.CharField(max_length=32, null=True)),
                ('homeCover', models.CharField(max_length=256, null=True)),
                ('joined', models.DateField(auto_now_add=True)),
                ('status', models.IntegerField(default=0)),
                ('wechatId', models.CharField(db_index=True, max_length=64, null=True)),
                ('weiboId', models.CharField(db_index=True, max_length=64, null=True)),
                ('inactive', models.BooleanField(default=False)),
                ('expired', models.DateField(null=True)),
            ],
            options={
                'db_table': 'Account_accountinfo',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leaderId', models.IntegerField(null=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('logo', models.CharField(max_length=256, null=True)),
                ('membersQuota', models.IntegerField(default=0)),
                ('description', models.TextField(null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'TOS_Core_organization',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OrganizationMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('memberId', models.IntegerField(unique=True)),
                ('group', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'TOS_Core_organizationmember',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TOSBetaApplication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('userId', models.IntegerField(null=True)),
                ('branchKey', models.CharField(max_length=32, null=True)),
                ('name', models.CharField(max_length=64)),
                ('phone', models.CharField(max_length=32, null=True)),
                ('email', models.EmailField(max_length=255, null=True)),
                ('type', models.IntegerField(default=0)),
                ('location', models.CharField(default='', max_length=255)),
                ('jobTitle', models.IntegerField(default=0)),
                ('countLevel', models.IntegerField(default=0)),
                ('organization', models.CharField(max_length=255)),
                ('customized', models.BooleanField(default=1)),
                ('description', models.TextField(null=True)),
                ('status', models.IntegerField(default=0)),
                ('foreigner', models.BooleanField(default=0)),
                ('contact', models.CharField(max_length=64, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'Pieceful_tosbetaapplication',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CodeAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.OneToOneField(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name='code', to='WechatApi.WechatAccount')),
            ],
        ),
        migrations.CreateModel(
            name='PromotionCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=16)),
                ('invitees', models.IntegerField(default=0)),
                ('applied', models.IntegerField(default=0)),
                ('usedBonus', models.IntegerField(default=0)),
                ('featured', models.BooleanField(default=False)),
                ('application', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='TOS_Pyramid.TOSBetaApplication')),
                ('creator', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='WechatApi.WechatAccount')),
                ('inviterCode', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='TOS_Pyramid.PromotionCode')),
                ('organization', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='promotionCodes', to='TOS_Pyramid.Organization')),
            ],
        ),
        migrations.AddField(
            model_name='codeaccount',
            name='code',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='TOS_Pyramid.PromotionCode'),
        ),
    ]
