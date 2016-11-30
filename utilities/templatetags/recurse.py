###############################################################################
# Recurse template tag for Django v1.1
# Copyright (C) 2008 Lucas Murray
# http://www.undefinedfire.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
###############################################################################

from django import template

register = template.Library()

class RecurseNode(template.Node):
    def __init__(self, var, name, condition, child, nodeList):
        self.var = var
        self.name = name
        self.condition = condition
        self.child = child
        self.nodeList = nodeList

    def __repr__(self):
        return '<RecurseNode>'

    def renderCallback(self, context, vals, level):
        output = []
        try:
            if len(vals):
                pass
        except:
            vals = [vals]
        if len(vals):
            if 'loop' in self.nodeList:
                output.append(self.nodeList['loop'].render(context))
            for val in vals:
                context.push()
                context['level'] = level
                context[self.name] = val

                if not self.condition or self.condition.resolve(context):
                    children = self.child.resolve(context)
                    context['children'] = children
                    if 'child' in self.nodeList:
                        output.append(self.nodeList['child'].render(context))
                        if children:
                            output.append(self.renderCallback(context, children, level + 1))
                    output.append(self.nodeList['endloop'].render(context))

                context.pop()
            output.append(self.nodeList['endrecurse'].render(context))
        return ''.join(output)

    def render(self, context):
        vals = self.var.resolve(context)
        output = self.renderCallback(context, vals, 1)
        return output

@register.tag
def recurse(parser, token):
    bits = list(token.split_contents())
    if not ((len(bits) == 6 or (len(bits) == 8 and bits[6] == 'if') and bits[2] == 'with' and bits[4] == 'as')):
        raise (template.TemplateSyntaxError, "Invalid tag syxtax, expected '{% recurse [childVar] with [parents] as [parent] (if [condition]) %}'")
    child = parser.compile_filter(bits[1])
    var = parser.compile_filter(bits[3])
    name = bits[5]
    condition = parser.compile_filter(bits[7]) if len(bits) == 8 else None

    nodeList = {}
    while len(nodeList) < 4:
        temp = parser.parse(('child','loop','endloop','endrecurse'))
        tag = parser.tokens[0].contents
        if tag == 'endloop' and 'loop' not in nodeList:
            raise (template.TemplateSyntaxError, "Invalid tag syxtax, '{% loop %}' should be followed by '{% endloop %}'")

        nodeList[tag] = temp
        parser.delete_first_token()
        if tag == 'endrecurse':
            break

    if "loop" in nodeList and "endloop" not in nodeList:
        raise (template.TemplateSyntaxError, "Invalid tag syxtax, '{% loop %}' should be followed by '{% endloop %}'")

    return RecurseNode(var, name, condition, child, nodeList)