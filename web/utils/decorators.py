from functools import wraps


def add_attrs(**attrs):
    """A decorator for setting attributes on a callable."""

    def decorator(func):
        for name, value in attrs.items():
            setattr(func, name, value)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
