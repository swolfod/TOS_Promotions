__author__ = 'Swolfod'
# -*- coding: utf-8 -*-

from django import template
register = template.Library()

@register.filter
def return_item(l, i):
    try:
        return l[i]
    except:
        return None