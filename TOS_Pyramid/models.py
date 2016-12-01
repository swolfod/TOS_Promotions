__author__ = "swolfod"


from django.db import models
from django.contrib.auth.models import User
from WechatApi.models import WechatAccount


class AccountInfo(models.Model):
    user         = models.OneToOneField(User, related_name="info", db_constraint=False)
    name         = models.CharField(max_length=64, db_index=True)
    birthday     = models.DateField(null=True)
    sex          = models.NullBooleanField(null=True)
    intro        = models.CharField(max_length=1024, default="")
    avatar       = models.CharField(max_length=256, null=True)
    phone        = models.CharField(max_length=32, null=True)
    homeCover    = models.CharField(max_length=256, null=True)
    joined       = models.DateField(auto_now_add=True)
    status       = models.IntegerField(default=0)

    wechatId     = models.CharField(max_length=64, null=True, db_index=True)
    weiboId      = models.CharField(max_length=64, null=True, db_index=True)

    inactive     = models.BooleanField(default=False)
    expired      = models.DateField(null=True)

    class Meta:
        managed = False
        db_table = 'Account_accountinfo'


class Organization(models.Model):
    leaderId        = models.IntegerField(null=True)
    name            = models.CharField(max_length=255, unique=True)
    logo            = models.CharField(max_length=256, null=True)
    membersQuota    = models.IntegerField(default=0)
    description     = models.TextField(null=True)
    created         = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'TOS_Core_organization'


class OrganizationMember(models.Model):
    memberId        = models.IntegerField(unique=True)
    organization    = models.ForeignKey(Organization, null=True, related_name="members")
    group           = models.IntegerField(default=0)
    created         = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "TOS_Core_organizationmember"


class TOSApplication(models.Model):
    name         = models.CharField(max_length=64)
    phone        = models.CharField(max_length=32, null=True)
    email        = models.EmailField(max_length=255, null=True)
    organization = models.CharField(max_length=255)
    approved     = models.BooleanField(default=False)
    created      = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "TOS_Pyramid"


class PromotionCode(models.Model):
    code        = models.CharField(max_length=16)
    invitees    = models.IntegerField(default=0)
    applied     = models.IntegerField(default=0)
    approved    = models.IntegerField(default=0)
    bonusDays   = models.IntegerField(default=0)
    usedBonus   = models.IntegerField(default=0)
    featured    = models.BooleanField(default=False)
    creator     = models.ForeignKey(WechatAccount, null=True)
    organization= models.ForeignKey(Organization, related_name="promotionCodes", null=True)
    inviterCode = models.ForeignKey("self", null=True)
    application = models.ForeignKey(TOSApplication, related_name="+", null=True)

    class Meta:
        app_label = "TOS_Pyramid"


class CodeAccount(models.Model):
    code        = models.ForeignKey(PromotionCode, related_name="accounts")
    account     = models.OneToOneField(WechatAccount, related_name="code", db_constraint=False, unique=True)

    class Meta:
        app_label = "TOS_Pyramid"
