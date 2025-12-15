from urllib.parse import urlencode

from django.http import HttpRequest
from django.template import Library

register = Library()


@register.simple_tag
def page_url(request: HttpRequest, page_number: int) -> str:
    """Append the page number to the query string parameters."""
    p = dict(request.GET.items())
    p["page"] = page_number
    return f"?{urlencode(sorted(p.items()))}"
