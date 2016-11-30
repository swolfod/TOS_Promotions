__author__ = 'swolfod'

from django import template
from django.template.defaulttags import URLNode, url
from utilities import djangoTLS

register = template.Library()

class AbsoluteURLNode(URLNode):
    def render(self, context):
        path = super(AbsoluteURLNode, self).render(context)
        request = context['request']
        absoluteUrl = request.build_absolute_uri(path)

        requireSecure =  djangoTLS.path_requires_secure(path)

        if requireSecure:
            absoluteUrl = absoluteUrl.replace('http://', 'https://')
        elif requireSecure is not None:
          absoluteUrl = absoluteUrl.replace('https://', 'http://')

        if self.asvar:
            context[self.asvar]= absoluteUrl
            return ''
        else:
            return absoluteUrl



@register.tag
def absurl(parser, token, node_cls=AbsoluteURLNode):
    """Just like {% url %} but ads the domain of the current site."""
    node_instance = url(parser, token)
    return node_cls(view_name=node_instance.view_name,
        args=node_instance.args,
        kwargs=node_instance.kwargs,
        asvar=node_instance.asvar)