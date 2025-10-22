import contextlib
from unittest import mock

import pytest


@pytest.fixture
def mock_super_method():
    """
    Fixture that mocks the super call in a method.

    Usage:
        # stuff.py
        class CoolClass:
            def example_method(self, foo):
                bar = super().example_method(foo)
                return frobnicate(bar)

        # test.py
        def test_example_method(mock_super_method):
            with mock_super_method(CoolClass.example_method, "mocked result"):
                assert foo.bar.example_method("baz") == frobnicate("mocked result")
    """

    @contextlib.contextmanager
    def inner(func, ret):
        module = func.__module__
        attr = func.__qualname__.rsplit(".", 1)[-1]
        with mock.patch(f"{module}.super") as super_mock:
            return_mock = super_mock.return_value
            return_mock.attach_mock(mock.Mock(return_value=ret), attr)
            yield

    return inner
