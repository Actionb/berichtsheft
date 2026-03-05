import tempfile
from enum import Enum
from io import BytesIO
from pathlib import Path

import requests
from django.contrib import messages
from django.http import FileResponse, HttpRequest
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import reverse

from web.models import Nachweis


class CONVERSION(Enum):
    """The 'type' to convert to PDF."""

    # As it stands, only HTML to PDF makes sense (see the note in url_to_pdf).

    HTML = "html"
    URL = "url"


def nachweis_to_pdf(
    request: HttpRequest,
    nachweis: Nachweis,
    redirect_url: str = "nachweis_list",
    **kwargs,
) -> FileResponse:
    """
    Generate FileResponse with a PDF of the given Nachweis object.

    Redirect to `redirect_url` if PDF generation failed.
    """
    kwargs = {"data": {"marginTop": 0, "marginRight": 0, "marginBottom": 0, "marginLeft": 0}, **kwargs}

    context = {"object": nachweis, "zfill_nummer": str(nachweis.nummer).zfill(3)}
    html = get_template("print.html").render(context, request)
    gotenberg_response = html_to_pdf(html, **kwargs)

    if not gotenberg_response.status_code == 200:
        messages.error(request, f"PDF Erzeugung fehlgeschlagen: {gotenberg_response.text}")
        return redirect(reverse(redirect_url))
    else:
        return FileResponse(BytesIO(gotenberg_response.content), as_attachment=True, filename=f"{nachweis.nummer}.pdf")


def _gotenberg_request(
    conversion: CONVERSION,
    base_url: str = "http://gotenberg:3000/forms/chromium/convert/",
    **kwargs,
) -> requests.Response:
    """Make a request against the gotenberg URL with the given conversion method."""
    return requests.post(url=f"{base_url}{conversion.value}", **kwargs)


def url_to_pdf(url: str, **kwargs) -> requests.Response:
    """Convert the document at the given URL into a PDF."""
    # NOTE: Doesn't work for URLs that require users to be authenticated!
    # The URL is requested by gotenberg, which does not have the required
    # session token/credentials.
    # NOTE: Also, this requires the gotenberg service to be included in the
    # ALLOWED_HOSTS setting!

    # 'url' is the only required form field:
    data = {"url": url, **kwargs.get("data", {})}
    # Content-Type must be 'multipart/form-data', so 'files' must be included -
    # even if redundant or empty:
    files = {"url": url, **kwargs.get("files", {None: ""})}
    return _gotenberg_request(CONVERSION.URL, data=data, files=files)


def html_to_pdf(html: str, **kwargs) -> requests.Response:
    """Convert the given HTML into a PDF."""
    # NOTE: gotenberg *requires* the file to be called 'index.html', so create
    # the file directly in a temporary directory, rather than using a
    # NamedTemporaryFile (which cannot have the *exact* name 'index.html').
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(Path(tmpdir) / "index.html", "w+") as f:  # '+' -> read and write
            f.write(html)
            f.seek(0)
            data = kwargs.get("data", {})
            files = {"file": f, **kwargs.get("files", {})}
            return _gotenberg_request(CONVERSION.HTML, data=data, files=files)
