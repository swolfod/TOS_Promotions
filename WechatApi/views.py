__author__ = 'swolfod'

from urllib.parse import unquote

from django.http import *
from django.shortcuts import HttpResponseRedirect
from utilities.djangoUtils import respondJson, respondErrorJson
from WechatApi.wechatUtils import refreshWechatToken, getWechatSignature, getCurrentAccount, requireWechatAuth
from utilities.djangoUtils import secureRender


def wechatSignature(request):
    echostr = request.GET.get("echostr")
    return HttpResponse(echostr)


def mpAuthCallback(request):
    state = request.GET.get("state", "")
    code = request.GET.get("code", None)

    if not code:
        return authFailed(request, state)

    try:
        refreshWechatToken(request=request, code=code, app="mp")
        redirectUrl = unquote(state) if state else "/"
        return HttpResponseRedirect(redirectUrl)
    except:
        #return authFailed(request, state)
        raise


def authFailed(request, state=""):
    if not state:
        state = request.GET.get("state", "")

    return HttpResponse("<h1>ERROR</h1>")


def apiSignature(request):
    pageUrl = request.GET["target"]
    appId, timestamp, nonceStr, signature = getWechatSignature(pageUrl)

    return respondJson({
        "appId": appId,
        "timestamp": timestamp,
        "nonceStr": nonceStr,
        "signature": signature,
    })


def testHome(request):
    return secureRender(request, "wechat/testHome.html", {})


@requireWechatAuth
def wechatAuthTest(request):
    wechatAccount = getCurrentAccount(request)

    return secureRender(request, "wechat/wechatAuthTest.html", {
        "account": wechatAccount
    })


def webAuthTest(request):
    return secureRender(request, "wechat/webAuthTest.html", {})


def payTest(request):
    return secureRender(request, "wechat/payTest.html", {})