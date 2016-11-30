__author__ = 'swolfod'

from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils.encoding import smart_str

ALWAYS_USE_TLS = getattr(settings, 'ALWAYS_USE_TLS', False)
USE_TLS = getattr(settings, 'USE_TLS', False)
SECURE_COMPATIBLE_PATHS = getattr(settings, 'SECURE_COMPATIBLE_PATHS', [])
SECURE_REQUIRED_PATHS = getattr(settings, 'SECURE_REQUIRED_PATHS', [])
DOMAIN_HOST = getattr(settings, 'DOMAIN_HOST', '')


def reverse_decorator(func):
    def inner(*args, **kwargs):
        # Call the real reverse function
        abs_path = func(*args, **kwargs)

        if not USE_TLS or not DOMAIN_HOST:
            # Short-circuit, no need to continue becuase there is no request we
            # can get smart with or TLS is turned off
            return abs_path

        secure = path_requires_secure(abs_path)

        if secure is not None:
            # Secure indicates either http or https and the request is not
            # currently being served that way
            protocol = 'https' if secure else 'http'
            abs_path = '%s://%s%s' % (protocol, DOMAIN_HOST, abs_path,)
        return abs_path
    return inner
urlresolvers.reverse = reverse_decorator(urlresolvers.reverse)


def path_requires_secure(path):
    if not SECURE_REQUIRED_PATHS:
        return None

    if not any([USE_TLS, ALWAYS_USE_TLS]):
        return None

    secure = None
    if ALWAYS_USE_TLS:
        # This site is setup to always use TLS so we set the secure bit to
        # always be true
        secure = True
    else:
        for securePath in SECURE_REQUIRED_PATHS:
            if path.startswith(securePath):
                secure = True
                break

    if secure is None and SECURE_COMPATIBLE_PATHS:
        secure = False
        for compatiblePath in SECURE_COMPATIBLE_PATHS:
            if path.startswith(compatiblePath):
                secure = None
                break

    return secure


def is_secure(request):
    """
    Determines if the given request is over HTTPS or not
    """
    if request.is_secure():
        return True

    #Handle the Webfaction case until this gets resolved in the request.is_secure()
    if 'HTTP_X_FORWARDED_SSL' in request.META:
        return request.META['HTTP_X_FORWARDED_SSL'] == 'on'

    return False


def self_redirect(request, secure, permanent=False):
    scheme = secure and 'https' or 'http'

    if request.scheme != scheme:
        newurl = '%s://%s%s' % (scheme, request.get_host(), request.get_full_path(),)

        if request.method == 'POST':
            raise RuntimeError('Django can\'t perform a TLS redirect while '
                'maintaining POST data.  Please structure your views so that '
                'redirects only occur during GETs.')

        return HttpResponsePermanentRedirect(newurl) if permanent else HttpResponseRedirect(newurl)


class TlsRedirect(object):
    def process_request(self, request):
        secure = path_requires_secure(request.path)

        # If secure is None, the require_tls was not present in the view
        # keyword args at all.  In this case, we don't want to redirect.
        # Leaving this keyword off probably indicates that the particular url
        # doesn't require http or https, we go with whatever we got
        if secure is not None and secure != is_secure(request):
            return self_redirect(request, secure)