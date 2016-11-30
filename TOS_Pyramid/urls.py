"""TOS_Pyramid URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import *
from .views import *

urlpatterns = [
    url(r'^wechat/', include('WechatApi.urls')),
    url(r'^admin/login$', adminAuth, name="TOS_Pyramid.views.adminAuth"),
    url(r'^admin/$', admin, name="TOS_Pyramid.views.admin"),
    url(r'^admin/exports$', exportPromotions, name="TOS_Pyramid.views.exportPromotions"),
    url(r'^search-organization/$', ajSearchOrganization, name="TOS_Pyramid.views.ajSearchOrganization"),
    url(r'^apply-tos/(\w+)/$', applyTOSBeta, name="TOS_Pyramid.views.applyTOSBeta"),
    url(r'^bind-code/(\w+)/$', bindCode, name="TOS_Pyramid.views.bindCode"),
    url(r'^share/(\w+)/$', shareCode, name="TOS_Pyramid.views.shareCode"),

]
