from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import User
from django.db.models.options import Options


def get_perm(action: str, opts: Options) -> str:
    """Return the permission name in the form <app_label>.<codename>."""
    return f"{opts.app_label}.{get_permission_codename(action, opts)}"


def has_add_permission(user: User, opts: Options) -> bool:
    return user.has_perm(get_perm("add", opts))


def has_change_permission(user: User, opts: Options) -> bool:
    return user.has_perm(get_perm("change", opts))


def has_delete_permission(user: User, opts: Options) -> bool:
    return user.has_perm(get_perm("delete", opts))
