__author__ = 'Swolfod'
# -*- coding: utf-8 -*-

import json
import time
import hashlib

from django.core.cache import cache
from django.conf import settings

from WechatApi.config import *
from WechatApi import wechatUtils
from utilities import utils


WECHAT_DEBUG = getattr(settings, "WECHAT_DEBUG", True)

def default(request):
    appId, timestamp, NonceStr, signature = wechatUtils.getWechatSignature(request.build_absolute_uri())

    return dict(request=request, appId=appId, timestamp=timestamp, nonceStr=NonceStr, signature=signature)