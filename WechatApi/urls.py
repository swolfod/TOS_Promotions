__author__ = 'Swolfod'
# -*- coding: utf-8 -*-

from django.conf.urls import *
from WechatApi.views import *

urlpatterns = [
   url(r"^wechatSignature/$", wechatSignature, name="WechatApi.views.wechatSignature"),
   url(r"^authCallback/$", mpAuthCallback, name="WechatApi.views.mpAuthCallback"),
   url(r"^apiSignature/$", apiSignature, name="WechatApi.views.apiSignature"),
   url(r"^tests/$", testHome, name="WechatApi.views.testHome"),
   url(r"^wechat-test/$", wechatAuthTest, name="WechatApi.views.wechatAuthTest"),
   url(r"^web-test/$", webAuthTest, name="WechatApi.views.webAuthTest"),
   url(r"^pay-test/$", payTest, name="WechatApi.views.payTest"),
]