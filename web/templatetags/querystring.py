from typing import Any
from urllib.parse import urlencode

from django.http import HttpRequest
from django.template import Library

register = Library()


def _get_querystring(request: HttpRequest, add: dict[str, Any] | None = None, remove: list[str] | None = None) -> str:
    """Add or remove query string parameters from the current request."""
    p = dict(request.GET.items())
    if add:
        for k, v in add.items():
            p[k] = v
    if remove:
        for k in remove:
            p.pop(k, None)
    return f"?{urlencode(sorted(p.items()))}"


@register.simple_tag
def add_qs(request: HttpRequest, name: str, value: Any) -> str:
    """Append a parameter to the query string of the current request."""
    return _get_querystring(request, add={name: value})


@register.simple_tag
def remove_qs(request: HttpRequest, name: str) -> str:
    """Remove a parameter from the query string of the current request."""
    return _get_querystring(request, remove=[name])
