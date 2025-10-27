import pytest

from tests.test_utils.models import TestModel
from web.utils.perms import has_add_permission, has_change_permission, has_delete_permission


@pytest.fixture
def opts():
    return TestModel._meta


def test_has_add_permission(user, opts, add_permission):
    assert not has_add_permission(user, opts)
    user = add_permission(user, "add", opts)
    assert has_add_permission(user, opts)


def test_has_change_permission(user, opts, add_permission):
    assert not has_change_permission(user, opts)
    user = add_permission(user, "change", opts)
    assert has_change_permission(user, opts)


def test_has_delete_permission(user, opts, add_permission):
    assert not has_delete_permission(user, opts)
    user = add_permission(user, "delete", opts)
    assert has_delete_permission(user, opts)
