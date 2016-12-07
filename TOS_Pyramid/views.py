__author__ = "swolfod"


import csv
from WechatApi.wechatUtils import getCurrentAccount, requireWechatAuth
from utilities.djangoUtils import secureRender, respondJson, ajaxErrorResponse
from utilities.utils import str2bool, randomString
from django.utils.translation import ugettext as _
from django.shortcuts import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from .models import *
from datetime import datetime, timedelta, date


@requireWechatAuth
@transaction.atomic
def bindCode(request, code):
    wechatAccount = getCurrentAccount(request)
    promotionCode = PromotionCode.objects.get(code=code)

    if request.method == "GET":
        currentCode = PromotionCode.objects.filter(accounts__account=wechatAccount).first()
        if not currentCode:
            CodeAccount(code=promotionCode, account=wechatAccount).save()

            if not promotionCode.bonusDays:
                promotionCode.bonusDays = 15
                promotionCode.save()

        elif currentCode.code != code:
            return secureRender(request, "confirmBindCode.html", {
                "account": wechatAccount,
                "promotionCode": promotionCode,
                "currentCode": currentCode
            })

        return HttpResponseRedirect(reverse("TOS_Pyramid.views.shareCode", args=(wechatAccount.id,)))
    elif request.method == "POST":
        toBind = str2bool(request.POST["bind"].strip().lower())
        if toBind:
            CodeAccount.objects.filter(account=wechatAccount).update(code=promotionCode)

            if not promotionCode.bonusDays:
                promotionCode.bonusDays = 15
                promotionCode.save()

        return HttpResponseRedirect(reverse("TOS_Pyramid.views.shareCode", args=(wechatAccount.id,)))



@requireWechatAuth
@transaction.atomic
def shareCode(request, accountId):
    wechatAccount = getCurrentAccount(request)
    promotionCode = PromotionCode.objects.filter(accounts__account=wechatAccount).first()

    if request.method == "POST":
        if promotionCode:
            return HttpResponseRedirect(reverse("TOS_Pyramid.views.shareCode", args=(wechatAccount.id,)))

        inviterId = request.POST.get("inviter")
        inviterCode = None
        if inviterId and inviterId != "000":
            inviter = WechatAccount.objects.get(pk=inviterId)
            inviterCode = PromotionCode.objects.get(accounts__account=inviter)
            inviterCode.invitees += 1
            inviterCode.save()

        code = randomString(8)
        while PromotionCode.objects.filter(code=code).exists():
            code = randomString(8)

        promotionCode = PromotionCode(code=code, creator=wechatAccount, bonusDays=15, inviterCode=inviterCode)
        promotionCode.save()

        CodeAccount(code=promotionCode, account=wechatAccount).save()

        return HttpResponseRedirect(reverse("TOS_Pyramid.views.shareCode", args=(wechatAccount.id,)))


    if not promotionCode:
        if accountId != "000":
            inviterAccount = WechatAccount.objects.get(pk=accountId)
        else:
            inviterAccount = {"id": "000", "nickname": "路书"}
        return secureRender(request, "invitee.html", {
            "account": wechatAccount,
            "inviter": inviterAccount
        })
    elif int(accountId) != wechatAccount.id:
        return HttpResponseRedirect(reverse("TOS_Pyramid.views.shareCode", args=(wechatAccount.id,)))
    elif promotionCode.organization or promotionCode.featured:
        return secureRender(request, "featuredInviter.html", {
            "account": wechatAccount,
            "promotionCode": {
                "id": promotionCode.id,
                "code": promotionCode.code,
                "invitees": promotionCode.invitees,
                "applied": promotionCode.applied,
                "approved": promotionCode.approved,
                "bonusDays": promotionCode.bonusDays,
                "usedBonus": promotionCode.usedBonus,
                "featured": promotionCode.featured,
                "organization": promotionCode.organization
            }
        })
    elif not promotionCode.application:
        return secureRender(request, "freshInviter.html", {
            "account": wechatAccount,
            "promotionCode": promotionCode
        })
    else:
        return secureRender(request, "featuredInviter.html", {
            "account": wechatAccount,
            "promotionCode": promotionCode
        })


def adminAuth(request):
    if request.method == "GET":
        return secureRender(request, "adminAuth.html", {})
    elif request.method == "POST":
        password = request.POST["password"].strip()
        if password == "Lushu123":
            maxAge = 24 * 60 * 60
            expires = (datetime.utcnow() + timedelta(seconds=maxAge)).strftime("%a, %d-%b-%Y %H:%M:%S GMT")
            response = HttpResponseRedirect(reverse("TOS_Pyramid.views.admin"))
            response.set_cookie("promotionauth", "promotionauth", max_age=maxAge, expires=expires)

            return response
        else:
            return secureRender(request, "adminAuth.html", {"invalidPassword": True})


@transaction.atomic
def admin(request):
    if "promotionauth" not in request.COOKIES:
        return HttpResponseRedirect(reverse("TOS_Pyramid.views.adminAuth"))

    start = int(request.GET.get("start", 0))
    q = request.GET.get("q")

    if request.method == "POST":
        organizationId = request.POST["organization"].strip().lower()

        code = randomString(8)
        while PromotionCode.objects.filter(code=code).exists():
            code = randomString(8)

        PromotionCode(code=code, organization_id=organizationId, featured=True).save()

        return HttpResponseRedirect(reverse("TOS_Pyramid.views.admin"))

    codeQuery = PromotionCode.objects.select_related("organization", "application").order_by("-featured", "-id")
    codeCount = codeQuery.count()

    if q:
        accounts = User.objects.filter(Q(email__icontains=q) | Q(info__phone__icontains=q)).values_list("id", flat=True)
        organizations = Organization.objects.filter(Q(members__memberId__in=accounts) | Q(name__icontains=q))
        codeQuery = codeQuery.filter(organization__in=organizations)

    promotionCodes = codeQuery[start: 50]

    prevStart = None
    nextStart = None

    if codeCount > 50:
        if start and start > 0:
            prevStart = start - 50 if start >= 50 else 0

        if (start or 0) + 50 < codeCount:
            nextStart = start + 50

    return secureRender(request, "admin.html", {
        "prevStart": prevStart,
        "nextStart": nextStart,
        "codes": promotionCodes,
        "query": q
    })


def ajSearchOrganization(request):
    query = request.GET.get("q", "")
    accounts = User.objects.filter(Q(email__icontains=query) | Q(info__phone__icontains=query)).values_list("id", flat=True)
    organizations = Organization.objects.filter(Q(members__memberId__in=accounts) | Q(name__icontains=query))[:10]

    return respondJson({
        "organizations": [{
            "id": organization.id,
            "name": organization.name
        } for organization in organizations]
    })


@transaction.atomic
def ajApproveApplication(request):
    appId = request.POST["application"]
    promotionCode = PromotionCode.objects.select_related("application", "inviterCode").get(application_id=appId)
    if not promotionCode.application.approved:
        promotionCode.application.approved = True
        promotionCode.application.save()

        if promotionCode.inviterCode:
            promotionCode.inviterCode.approved += 1
            promotionCode.inviterCode.bonusDays += 15
            promotionCode.inviterCode.save()

    return respondJson()


@requireWechatAuth
@transaction.atomic
def applyTOSBeta(request, code):
    wechatAccount = getCurrentAccount(request)
    responseContent = {"account": wechatAccount, "code": code}

    promotionCode = PromotionCode.objects.get(code=code)
    if promotionCode.application:
        responseContent["existed"] = True
        return secureRender(request, "applyTOS.html", responseContent)

    if request.method == "POST":
        name = request.POST["name"].strip()
        phone = request.POST["phone"].strip()
        email = request.POST["email"].strip()
        organization = request.POST["organization"].strip()
        code = request.POST["code"]

        promotionCode = PromotionCode.objects.get(code=code)
        if promotionCode.application_id:
            responseContent["error"] = "您已申请过了.请耐心等候我们的回复."

        users = User.objects.filter(Q(email=email) | Q(info__phone="phone")).values_list("id", flat=True)
        if users:
            members = OrganizationMember.objects.filter(memberId__in=users)
            if members:
                responseContent["error"] = "这个邮箱/手机号码已经注册过了"

        application = TOSApplication(name=name, phone=phone, email=email, organization=organization)
        application.save()

        promotionCode.application = application
        promotionCode.save()

        if promotionCode.inviterCode:
            promotionCode.inviterCode.applied += 1
            promotionCode.inviterCode.bonusDays += 2
            promotionCode.inviterCode.save()

        return secureRender(request, "applicationSubmitted.html" if not responseContent.get("error") else "applyTOS.html", responseContent)
    else:
        return secureRender(request, "applyTOS.html", responseContent)

def exportPromotions(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="promotions_{}.csv"'.format(date.today().strftime("%Y%m%d"))
    writer = csv.writer(response)
    writer.writerow(["优惠码", "对应机构", "接受邀请数","邀请申请数", "邀请开通数", "需奖励总天数", "已奖励天数"])

    q = request.GET.get("q")

    codeQuery = PromotionCode.objects.select_related("organization").order_by("-featured", "-id")

    if q:
        accounts = User.objects.filter(Q(email__icontains=q) | Q(info__phone__icontains=q)).values_list("id", flat=True)
        organizations = Organization.objects.filter(Q(members__memberId__in=accounts) | Q(name__icontains=q))
        codeQuery = codeQuery.filter(organization__in=organizations)

    promotionCodes = codeQuery.all()

    for code in promotionCodes:
        organizationName = code.organization.name if code.organization else ""

        writer.writerow([code.code, organizationName, code.invitees, code.applied, code.approved, code.bonusDays, code.usedBonus])

    return response