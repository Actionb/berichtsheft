from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.options import Options

from web import models as _models


def get_perm(action: str, opts: Options) -> str:
    """Return the permission name in the form <app_label>.<codename>."""
    return f"{opts.app_label}.{get_permission_codename(action, opts)}"


def has_add_permission(user: User, opts: Options) -> bool:
    return user.has_perm(get_perm("add", opts))


def has_change_permission(user: User, opts: Options) -> bool:
    return user.has_perm(get_perm("change", opts))


def has_delete_permission(user: User, opts: Options) -> bool:
    return user.has_perm(get_perm("delete", opts))


def add_user_permissions(user):
    """Give the user default permissions to use the app."""
    # TODO: implement this by assigning the user a group with the appropriate
    # permissions. Create the group via data migration?
    permissions = []
    for model in [_models.Nachweis, _models.Abteilung]:
        for action in ["add", "change", "view", "delete"]:
            perm = Permission.objects.get(
                codename=get_permission_codename(action, model._meta),
                content_type=ContentType.objects.get_for_model(model),
            )
            permissions.append(perm)
    user.user_permissions.set(permissions)
