__author__ = 'swolfod'

from urllib.parse import quote_plus
from uuid import uuid1
from random import randint
import json
from datetime import datetime, timedelta
from django.core import cache
import hashlib
import time
import requests
import xmltodict

from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.utils.translation import ugettext as _

from .config import *
from utilities import djangoUtils, utils
from WechatApi.models import *


WECHAT_DEBUG = getattr(settings, "WECHAT_DEBUG", True)
cacheClient = cache.caches["redis"]


def authenticated(request):
    if WECHAT_DEBUG:
        return True

    unionid = request.session.get("unionid")
    refreshToken = request.session.get("refreshToken")

    return unionid is not None and refreshToken is not None


def wechatAuthUrl(request, state=""):
    return "https://open.weixin.qq.com/connect/oauth2/authorize?appid={0}&redirect_uri={1}&response_type=code&scope=snsapi_base,snsapi_userinfo&state={2}#wechat_redirect".format(
        AppId["mp"],
        quote_plus(request.build_absolute_uri(reverse("WechatApi.views.mpAuthCallback"))),
        state
    )


def requireWechatAuth(oriFunc):
    def wrapper(request,  *args, **kwargs):
        if authenticated(request):
            return oriFunc(request,  *args, **kwargs)

        return HttpResponseRedirect(wechatAuthUrl(request, quote_plus(request.get_full_path())))

    return wrapper


def wechatPayCallback(*args, **kwargs):
    if len(args) > 0:
        oriFunc = args[0]

        def wrapper(instance, request, *args, **kwargs):
            if request.method != "POST":
                return HttpResponse("<h1>ERROR</h1>")

            body_unicode = request.body.decode('utf-8')
            orderInfo = xmltodict.parse(body_unicode)["xml"]
            sign = orderInfo["sign"]
            del orderInfo["sign"]

            if sign !=  wechatPaySignature(orderInfo):
                return HttpResponse(utils.dict2xml({
                    "xml": {
                        "return_code": "FAIL",
                        "return_msg": _("Invalid Signature")
                    }
                }, True))

            request.wechatPayInfo = orderInfo
            oriFunc(instance, request,  *args, **kwargs)

            return HttpResponse(utils.dict2xml({
                "xml": {
                    "return_code": "SUCCESS",
                    "return_msg": "OK"
                }
            }, True))

        return wrapper

    def _decorator(oriFunc):
        return wechatPayCallback(oriFunc, **kwargs)

    return _decorator


def getAccountById(unionid):
    return djangoUtils.getOrNone(WechatAccount, unionid=unionid)


def getCurrentAccount(request):
    unionid = request.session.get("unionid")
    if not WECHAT_DEBUG:
        accessToken = request.session.get("accessToken")
        accessExpiry = request.session.get("accessExpiry")
        if not accessToken or not accessExpiry or datetime.strptime(accessExpiry, '%Y-%m-%d %H:%M:%S') < datetime.now():
            refreshWechatToken(request=request, app=request.session["app"], refreshToken=request.session["refreshToken"])
            unionid = request.session["unionid"]

    account = getAccountById(unionid)

    if not account and WECHAT_DEBUG:
        account = WechatAccount(
            unionid = uuid1().hex,
            openid = uuid1().hex,
            nickname = DEBUG_USERS[randint(0, len(DEBUG_USERS) - 1)],
            sex = randint(0, 1) == 0,
            headimgurl = DEBUG_AVATARS[randint(0, len(DEBUG_AVATARS) - 1)]
        )

        account.save()
        request.session["unionid"] = account.unionid

        return account

    return account


def refreshWechatToken(code=None, app="mp", refreshToken=None, request=None, createSession=True):
    if code:
        accessUrl = "https://api.weixin.qq.com/sns/oauth2/access_token?appid={0}&secret={1}&code={2}&grant_type=authorization_code".format(
            AppId[app],
            SecretKey[app],
            code
        )
    elif refreshToken:
        accessUrl = "https://api.weixin.qq.com/sns/oauth2/refresh_token?appid={0}&grant_type=refresh_token&refresh_token={1}".format(AppId[app], refreshToken)
    else:
        raise Exception()

    link, content, session = utils.LoadHttpString(accessUrl, encoding="utf-8", timeout=10)
    accessInfo = json.loads(content)

    if accessInfo.get("errmsg"):
        raise Exception(accessInfo["errmsg"])

    access_token = accessInfo["access_token"]
    accessExpires = int(accessInfo["expires_in"])
    openid = accessInfo["openid"]

    userInfoUrl = "https://api.weixin.qq.com/sns/userinfo?access_token={0}&openid={1}&lang=zh_CN".format(access_token, openid)
    link, content, session = utils.LoadHttpString(userInfoUrl, session=session, encoding="utf-8", timeout=10)

    userInfo = json.loads(content)
    unionid = userInfo["unionid"]

    if request and createSession:
        request.session["app"] = app
        request.session["accessToken"] = access_token
        request.session["accessExpiry"] = (datetime.now() + timedelta(0, accessExpires)).strftime('%Y-%m-%d %H:%M:%S')
        request.session["refreshToken"] = accessInfo["refresh_token"]
        request.session["unionid"] = unionid
        request.session["scope"] = accessInfo["scope"]

        # Refresh token expires in 30 days
        request.session.set_expiry(3600 * 24 * 30)

    wechatAccount = djangoUtils.getOrNone(WechatAccount, unionid=unionid)
    if not wechatAccount:
        wechatAccount = WechatAccount(unionid=unionid)

    wechatAccount.nickname = userInfo["nickname"]
    wechatAccount.openid = userInfo["openid"]
    wechatAccount.sex = int(userInfo.get("sex", 1)) == 1
    wechatAccount.province = userInfo.get("province", None)
    wechatAccount.city = userInfo.get("city", None)
    wechatAccount.country =  userInfo.get("country", None)
    wechatAccount.headimgurl = userInfo.get("headimgurl", None)
    wechatAccount.privilege = userInfo.get("privilege", None)

    wechatAccount.save()

    return accessInfo, wechatAccount


def getWechatSignature(pageUrl):
    if WECHAT_DEBUG:
        return dict()

    appId = AppId["mp"]

    jsapi_ticket = cacheClient.get("jsapi_ticket")
    if not jsapi_ticket:
        access_token = cacheClient.get("access_token")
        if not access_token:
            tokenUrl = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={0}&secret={1}".format(appId, SecretKey)
            link, content, session = utils.LoadHttpString(tokenUrl)
            accessInfo = json.loads(content)
            access_token = accessInfo.get("access_token")
            if access_token:
                cacheClient.set("access_token", access_token, 7200)

        if access_token:
            ticketUrl = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={0}&type=jsapi".format(access_token)
            link, content, session = utils.LoadHttpString(ticketUrl)
            ticketInfo = json.loads(content)
            jsapi_ticket = ticketInfo.get("ticket")
            if jsapi_ticket:
                cacheClient.set("jsapi_ticket", jsapi_ticket, 7200)

    signature = None
    timestamp = str(int(time.time()))
    if jsapi_ticket:
        rawStr = "jsapi_ticket={0}&noncestr={1}&timestamp={2}&url={3}".format(
            jsapi_ticket,
            NonceStr,
            timestamp,
            pageUrl
        )
        signature = hashlib.sha1(rawStr.encode("utf-8")).hexdigest()

    return appId, timestamp, NonceStr, signature


def createPayment(request, tradeType, body, amount, orderId, callbackUrl, startTime=None, endTime=None, openId=None, details=None):

    orderInfo = {
        "xml": {
            "appid": AppId["mp"],
            "body": body,
            "mch_id": MerchantId,
            "nonce_str": utils.randomString(),
            "notify_url": callbackUrl,
            "trade_type": tradeType,
            "total_fee": str(amount),
            "out_trade_no": orderId,
            "spbill_create_ip": djangoUtils.getClientIp(request),
        }
    }

    if tradeType == "JSAPI" and openId:
        orderInfo["xml"]["openid"] = openId

    if details:
        orderInfo["xml"]["detail"] = details

    if startTime and endTime:
        orderInfo["xml"]["time_start"] = startTime
        orderInfo["xml"]["time_expire"] = endTime

    orderInfo["xml"]["sign"] = wechatPaySignature(orderInfo["xml"])
    xmlOrderInfo = utils.dict2xml(orderInfo, True)
    response = requests.post("https://api.mch.weixin.qq.com/pay/unifiedorder", data=xmlOrderInfo.encode("utf-8"))
    responseInfo = xmltodict.parse(response.text.encode("utf-8"))["xml"]

    payInfo =  {
        "prepay_id": responseInfo["prepay_id"]
    }

    if tradeType == "NATIVE":
        payInfo["code_url"] = responseInfo["code_url"]

    return payInfo


def wechatPaySignature(orderInfo):
    encodeStr = "&".join("{0}={1}".format(k, v) for k, v in sorted(orderInfo.items()))
    encodeStr += "&key=" + MerchantKey
    return hashlib.md5(encodeStr.encode('utf-8')).hexdigest().upper()