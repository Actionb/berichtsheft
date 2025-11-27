from typing import Any

from django.db.models import Model
from django.template import Library
from django.utils.safestring import SafeString

from web.actions import ListAction

register = Library()


@register.simple_tag
def render_action(action: ListAction, request: Any, obj: Model) -> SafeString:
    """Render the given action button."""
    return action.render(request, obj)
