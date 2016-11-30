__author__ = 'swolfod'

from django import template
import re


register = template.Library()

@register.simple_tag
def wechatAccountHeadImg(headImgUrl, size=0):
    return re.sub(r"/[0-9]+$", "/" + str(size), headImgUrl)
