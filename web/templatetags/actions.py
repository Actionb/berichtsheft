from collections import OrderedDict

from django.http import HttpRequest
from django.template import Library
from django.utils.safestring import SafeString

from web.actions import ListAction

register = Library()


@register.simple_tag
def render_action(action: ListAction, request: HttpRequest, row: OrderedDict) -> SafeString:
    """Render the action button for the given row of results."""
    return action.render(request, row)
