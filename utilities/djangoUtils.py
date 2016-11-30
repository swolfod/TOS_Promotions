__author__ = 'Swolfod'
# -*- coding: utf-8 -*-

from django.template.context_processors import csrf
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, render_to_response
from django.core.exceptions import SuspiciousOperation
from io import FileIO, BufferedWriter
import json
import re
import decimal
from django.views.generic import TemplateView
from django.template import RequestContext
from datetime import datetime, timedelta
from django.http import *
import logging
from django.core.serializers.json import DjangoJSONEncoder
from urllib.parse import urlparse
from django.conf import settings
from hashids import Hashids
from django.core.cache import caches
from django.db import models


SECRET_KEY = getattr(settings, 'SECRET_KEY', False)
REDIS_HOST = getattr(settings, "REDIS_HOST", "127.0.0.1")
REDIS_PORT = getattr(settings, "REDIS_PORT", 6379)


def getOrNone(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


def getOrCreate(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        entity = model(**kwargs)
        entity.save()
        return entity

def queryAll(model, **kwargs):
    return model.objects.filter(**kwargs).all()


def secureRender(request, template, dic, userContext=True):
    dic.update(csrf(request))
    if userContext:
        return render_to_response(template, dic, context_instance=RequestContext(request))
    else:
        return render_to_response(template, dic)


def ajaxResponse(context=None, success=True):
    if not context:
        context = {}

    return {"success": True if success else False, "result": context}


def respondJson(context=None, success=True):
    responseStr = json.dumps(ajaxResponse(context, success), cls=DjangoJSONEncoder)
    return HttpResponse(responseStr)


def ajaxErrorResponse(errMsg, errCode=None):
    context = {"errMsg": errMsg}
    if errCode is not None:
        context["errCode"] = errCode

    return ajaxResponse(context, False)


def respondErrorJson(errMsg, errCode=None):
    responseStr = json.dumps(ajaxErrorResponse(errMsg, errCode), cls=DjangoJSONEncoder)
    return HttpResponse(responseStr)


def getCurrentUser(request):
    if request.user.is_authenticated():
        return request.user

    return None


def encodedCurrentUserId(request):
    currentUser = getCurrentUser(request)
    return encodeId(currentUser.id) if currentUser else None


def save_upload(uploaded, filename, raw_data ):
    """
    raw_data: if True, uploaded is an HttpRequest object with the file being
              the raw post data
              if False, uploaded has been submitted via the basic form
              submission and is a regular Django UploadedFile in request.FILES
    """
    try:
        with BufferedWriter( FileIO( filename, "wb" ) ) as dest:
            # if the "advanced" upload, read directly from the HTTP request
            # with the Django 1.3 functionality
            if raw_data:
                foo = uploaded.read( 1024 )
                while foo:
                    dest.write( foo )
                    foo = uploaded.read( 1024 )
                    # if not raw, it was a form upload so read in the normal Django chunks fashion
            else:
                for c in uploaded.chunks():
                    dest.write(c)
                # got through saving the upload, report success
            return True
    except IOError:
        # could not open the file most likely
        pass
    return False


class AnonymousRequired(object):
    def __init__(self, view_function, redirect_to):
        if redirect_to is None:
            from django.conf import settings
            redirect_to = settings.LOGIN_REDIRECT_URL
        self.view_function = view_function
        self.redirect_to = redirect_to

    def __call__(self, request, *args, **kwargs):
        if request.user is not None and request.user.is_authenticated():
            return HttpResponseRedirect(self.redirect_to)
        return self.view_function(request, *args, **kwargs)


def anonymous_required(view_function, redirect_to=None):
    return AnonymousRequired(view_function, redirect_to)


def addParameter(url, parName, parVar):
    prefix = "?" if "?" not in url else "&"
    return url + prefix + parName + "=" + parVar


class DirectTemplateView(TemplateView):
    extra_context = None
    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            for key, value in self.extra_context.items():
                if callable(value):
                    context[key] = value()
                else:
                    context[key] = value
        return context


class DefaultJSONEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, decimal.Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])
        return super(DefaultJSONEncoder, self)._iterencode(o, markers)


class ForceAcceptJsonMiddleware(object):
    """
    Ignore Accept-Language HTTP headers

    This will force the I18N machinery to always choose settings.LANGUAGE_CODE
    as the default initial language, unless another one is set via sessions or cookies

    Should be installed *before* any middleware that checks request.META['HTTP_ACCEPT_LANGUAGE'],
    namely django.middleware.locale.LocaleMiddleware
    """
    def process_request(self, request):
        acceptHeader = request.META.get("HTTP_ACCEPT")
        if not acceptHeader:
            acceptHeader = "application/json; charset=utf-8"
        elif "application/json" not in acceptHeader:
            acceptHeader = "application/json; indent=4, " + acceptHeader + "; charset=utf-8"

        request.META["HTTP_ACCEPT"] = acceptHeader


class ForceDefaultLanguageMiddleware(object):
    """
    Ignore Accept-Language HTTP headers

    This will force the I18N machinery to always choose settings.LANGUAGE_CODE
    as the default initial language, unless another one is set via sessions or cookies

    Should be installed *before* any middleware that checks request.META['HTTP_ACCEPT_LANGUAGE'],
    namely django.middleware.locale.LocaleMiddleware
    """
    def process_request(self, request):
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']


djangoLogger = logging.getLogger('django')

class WsgiLogErrors(object):
    def process_exception(self, request, exception):
        url = request.build_absolute_uri()
        djangoLogger.error('\n\n============EXCEPTION: {0}\n{1}\n\n'.format(url, datetime.now()))


class DisableCSRFCheck(object):
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)


def SmartTruncate(content, length=100, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix


def pageItems(query, page, itemPerPage):
    page = int(page)
    if page < 1:
        page = 1

    startNum = (page - 1) * itemPerPage
    endNum = startNum + itemPerPage + 1

    items = query.all()[startNum:endNum]

    if not items and page > 1:
        count = query.count()
        page = (count - 1) // itemPerPage + 1
        startNum = (page - 1) * itemPerPage
        endNum = startNum + itemPerPage + 1
        items = query.all()[startNum:endNum]

    previousPage = page - 1
    nextPage = page + 1 if len(items) > itemPerPage else 0
    if items:
        items = items[:len(items) - 1]

    return items, previousPage, nextPage


def delta2dict( delta ):
    """Accepts a delta, returns a dictionary of units"""
    delta = abs( delta )
    return {
        'year'   : int(delta.days / 365),
        'month'  : int(delta.days / 30),
        'day'    : int(delta.days % 365),
        'hour'   : int(delta.seconds / 3600),
        'minute' : int(delta.seconds / 60) % 60,
        'second' : delta.seconds % 60,
        'microsecond' : delta.microseconds
    }


def human(dt, precision=1, past_tense='{} ago', future_tense='in {}'):
    """Accept a datetime or timedelta, return a human readable delta string"""
    delta = dt
    if type(dt) is not type(timedelta()):
        delta = datetime.now() - dt

    the_tense = past_tense
    if delta < timedelta(0):
        the_tense = future_tense

    d = delta2dict( delta )
    hlist = []
    count = 0
    units = ( 'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond' )
    for unit in units:
        if count >= precision: break # met precision
        if d[ unit ] == 0: continue # skip 0's
        s = '' if d[ unit ] == 1 else 's' # handle plurals
        hlist.append( '%s %s%s' % ( d[unit], unit, s ) )
        count += 1
    human_delta = ', '.join( hlist )
    return the_tense.format(human_delta)


def crossOrigin(oriFunc):
    XS_SHARING_ALLOWED_ORIGINS = '*'
    XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']
    XS_SHARING_ALLOWED_HEADERS = ['*', 'X-Requested-With', 'origin', 'x-csrftoken', 'content-type', 'accept']
    XS_SHARING_ALLOWED_CREDENTIALS = 'true'

    def wrapper(request, *args):
        origin = request.META['HTTP_ORIGIN'] if 'HTTP_ORIGIN' in request.META else None
        if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META:
            response = HttpResponse()
        else:
            response = oriFunc(request, *args)

        if response and isinstance(response, HttpResponse):
            response['Access-Control-Allow-Origin']  = origin if origin else XS_SHARING_ALLOWED_ORIGINS
            response['Access-Control-Allow-Methods'] = ",".join( XS_SHARING_ALLOWED_METHODS )
            response['Access-Control-Allow-Headers'] = ",".join( XS_SHARING_ALLOWED_HEADERS )
            response['Access-Control-Allow-Credentials'] = XS_SHARING_ALLOWED_CREDENTIALS

        return response

    return wrapper


def extractDomain(netloc):
    if ":" in netloc:
        netloc = netloc[:netloc.index(":")]

    return netloc[netloc.index(".") + 1:]

    lastDotIdx = netloc.rindex(".")
    dotIdx = netloc.index(".")
    while dotIdx != lastDotIdx:
        netloc = netloc[dotIdx + 1:]
        dotIdx = netloc.index(".")
        lastDotIdx = netloc.rindex(".")

    return netloc


def isOurSite(url, request):
    targetHost = urlparse(url).netloc
    ourHost = urlparse(request.build_absolute_uri()).netloc

    return targetHost == ourHost or extractDomain(targetHost) == extractDomain(ourHost)


def encodeId(id):
    if id == None:
        return ""

    return encodeIdList([id])


def decodeId(hash):
    if not hash:
        return None

    try:
        return decodeIdList(hash)[0]
    except:
        raise Http404


_encoder = Hashids(SECRET_KEY, 8)
_idDict = {}
_hashDict = {}
def encodeIdList(idList):
    if not idList:
        return ""

    if len(idList) == 1 and int(idList[0]) < 1000000:
        id = int(idList[0])
        encodedHash = _hashDict.get(id)
        if encodedHash == None:
            encodedHash = _encoder.encode(id)
            _idDict[encodedHash] = id
            _hashDict[id] = encodedHash

        return encodedHash

    return _encoder.encode(*[int(id) for id in idList])


def decodeIdList(hash):
    if not hash or not hash.strip():
        return []

    hash = hash.strip()
    id = _idDict.get(hash)
    if id != None:
        return [id]

    idList = [int(id) for id in _encoder.decode(hash)]
    if hash and not idList:
        raise Http404

    if len(idList) == 1 and idList[0] < 1000000:
        _hashDict[idList[0]] = hash
        _idDict[hash] = idList[0]
    return idList


def getCacheClient():
    return caches["redis"]


def combineHashes(hashList):
    idList = sum([decodeIdList(hash) for hash in hashList if hash], [])
    return encodeIdList(idList)


USE_X_FORWARDED_FOR = getattr(settings, 'USE_X_FORWARDED_FOR', True)
ip_validation_re = re.compile(r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$")
def getClientIp(request):
    if USE_X_FORWARDED_FOR and 'HTTP_X_FORWARDED_FOR' in request.META:
        addr = request.META['HTTP_X_FORWARDED_FOR'].split(",",1)[0].strip()
    elif 'REMOTE_ADDR' in request.META:
        addr = request.META['REMOTE_ADDR']
    else:
        addr = "127.0.0.1" #Couldn't determine actual client IP!

    if not ip_validation_re.match(addr):
        raise SuspiciousOperation("Invalid client IP: %s" % addr)

    return addr


def getCurrentTimeStamp():
    return int(datetime.now().timestamp()*1000)


class TimeStampField(models.BigIntegerField):

    def __init__(self, verbose_name=None, name=None, auto_now=False,
                 auto_now_add=False, **kwargs):
        self.auto_now, self.auto_now_add = auto_now, auto_now_add
        if auto_now or auto_now_add:
            kwargs['editable'] = False
            kwargs['blank'] = True
        super(TimeStampField, self).__init__(verbose_name, name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(TimeStampField, self).deconstruct()
        if self.auto_now is not False:
            kwargs["auto_now"] = self.auto_now
        if self.auto_now_add is not False:
            kwargs["auto_now_add"] = self.auto_now_add
        if self.auto_now or self.auto_now_add:
            del kwargs['blank']
            del kwargs['editable']
        return name, path, args, kwargs

    def pre_save(self, model_instance, add):
        if self.auto_now or (self.auto_now_add and add):
            value = getCurrentTimeStamp()
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(TimeStampField, self).pre_save(model_instance, add)
