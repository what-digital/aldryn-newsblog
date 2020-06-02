from cms.templatetags.cms_tags import RenderPlaceholder
from django import template

register = template.Library()


class RenderPlaceholderNoCache(RenderPlaceholder):

    name = 'render_placeholder_no_cache'

    def get_value_for_context(self, context, **kwargs):
        return self._get_value(context, nocache=True, editable=False, **kwargs)

    def get_value(self, context, **kwargs):
        return self._get_value(context, nocache=True, **kwargs)


register.tag('render_placeholder_no_cache', RenderPlaceholderNoCache)
