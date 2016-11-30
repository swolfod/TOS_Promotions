__author__ = 'Swolfod'
# -*- coding: utf-8 -*-

from .djangoUtils import getCurrentUser

def default(request):
    return dict(request=request, loggedInUser=getCurrentUser(request))