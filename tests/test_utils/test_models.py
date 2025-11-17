from unittest import mock

import pytest

from web.utils.models import _get_soft_delete_models, collect_deleted_objects

from .models import SoftDeleteTestModel


@pytest.fixture
def obj(user):
    return SoftDeleteTestModel.objects.create(name="Foo", user=user)


@pytest.fixture
def deleted_obj(user):
    """Create an object that has been deleted."""
    obj = SoftDeleteTestModel.objects.create(name="Bar", user=user)
    obj.delete()
    return obj


@pytest.fixture
def not_user_obj(superuser):
    """Create an object that has also been deleted, but belongs to another user."""
    obj = SoftDeleteTestModel.objects.create(name="Baz", user=superuser)
    obj.delete()
    return obj


def test_get_soft_delete_models():
    """Assert that _get_soft_delete_models returns the expected models."""
    assert list(_get_soft_delete_models("test_utils")) == [SoftDeleteTestModel]


def test_collect_deleted_objects(user, obj, deleted_obj, not_user_obj):
    """Assert that collect_deleted_objects returns the expected items."""
    with mock.patch("web.utils.models._get_soft_delete_models", new=mock.Mock(return_value=[SoftDeleteTestModel])):
        objs = collect_deleted_objects(user)
    queryset = objs[0]
    assert deleted_obj in queryset
    assert obj not in queryset
    assert not_user_obj not in queryset
