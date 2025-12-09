from typing import Any

from django.http import HttpRequest
from django.template import Library
from django.utils.safestring import SafeString

from web.actions import ListAction

register = Library()


@register.simple_tag
def render_action(action: ListAction, request: HttpRequest, **kwargs: Any) -> SafeString:
    """Render the given action button."""
    return action.render(request, **kwargs)
