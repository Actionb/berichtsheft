import pytest

from web.templatetags import querystring


@pytest.mark.parametrize(
    "request_data, kwargs, expected",
    [
        ({}, {}, "?"),
        ({"foo": "bar"}, {"remove": {"foo": "bar"}}, "?"),
        ({"foo": "bar"}, {"add": {"spam": "egg"}}, "?foo=bar&spam=egg"),
    ],
)
def test_get_querystring(rf, request_data, kwargs, expected):
    request = rf.get(path="", data=request_data)
    assert querystring._get_querystring(request, **kwargs) == expected


@pytest.mark.parametrize(
    "request_data, name, value, expected",
    [({}, "spam", "egg", "?spam=egg"), ({"foo": "bar"}, "spam", "egg", "?foo=bar&spam=egg")],
)
def test_add_qs(rf, request_data, name, value, expected):
    request = rf.get(path="", data=request_data)
    assert querystring.add_qs(request, name, value) == expected


@pytest.mark.parametrize(
    "request_data, name, expected",
    [
        ({"foo": "bar"}, "spam", "?foo=bar"),
        ({"foo": "bar"}, "foo", "?"),
    ],
)
def test_remove_qs(rf, request_data, name, expected):
    request = rf.get(path="", data=request_data)
    assert querystring.remove_qs(request, name) == expected


@pytest.mark.parametrize("query_string, expected", [("/?page=2", "?unfinished=1"), ("/?unfinished=1&foo=2", "?foo=2")])
def test_nachweis_status(rf, query_string, expected):
    request = rf.get(query_string)
    assert querystring.nachweis_status(request, "unfinished") == expected
