from django.conf import settings
from django.contrib.auth import get_permission_codename
from django.contrib.auth.models import AbstractUser, Group
from django.db.models import Model
from django.db.models.options import Options


def get_perm(action: str, opts: Options) -> str:
    """Return the permission name in the form <app_label>.<codename>."""
    return f"{opts.app_label}.{get_permission_codename(action, opts)}"


def has_add_permission(user: AbstractUser, opts: Options) -> bool:
    return user.has_perm(get_perm("add", opts))


def has_change_permission(user: AbstractUser, opts: Options) -> bool:
    return user.has_perm(get_perm("change", opts))


def has_delete_permission(user: AbstractUser, opts: Options) -> bool:
    return user.has_perm(get_perm("delete", opts))


def add_azubi_permissions(user):
    """Give the user default 'Azubi' permissions to use the app."""
    user.groups.add(Group.objects.get(name=settings.AZUBI_GROUP_NAME))


def is_owner(user: AbstractUser, obj: Model) -> bool:
    """Return whether the given is the owner of the object."""
    return user == obj.user


def can_delete(user: AbstractUser, obj: Model) -> bool:
    """Return whether the given user may delete (soft/hard) the given obj."""
    return is_owner(user, obj) and has_delete_permission(user, obj._meta)
