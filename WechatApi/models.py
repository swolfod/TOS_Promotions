__author__ = 'swolfod'

from django.db import models


class WechatAccount(models.Model):
    openid          = models.CharField(max_length=255, unique=True)
    unionid         = models.CharField(max_length=255, unique=True)
    nickname        = models.CharField(max_length=255)
    sex             = models.BooleanField(default=False)
    province        = models.CharField(max_length=255, null=True)
    city            = models.CharField(max_length=255, null=True)
    country         = models.CharField(max_length=255, null=True)
    headimgurl      = models.CharField(max_length=255, null=True)
    privilege       = models.CharField(max_length=255, null=True)

    def __unicode__(self):
        return self.nickname

    class Meta:
        app_label = "WechatApi"