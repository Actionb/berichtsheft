from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_permission_codename
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate
from django.dispatch import receiver


def _assure_permissions_created():  # pragma: no cover
    """Ensure that permissions for the web app have been created."""
    # Permissions are created during the post_migrate signal. Since we can't be
    # sure that the permissions have been created when any of our own receivers
    # are run, we explicitly call the Django function that creates the
    # Permissions for the web app:
    create_permissions(apps.get_app_config(app_label="web"), verbosity=0)


@receiver(post_migrate, dispatch_uid="create_azubi_group")
def create_azubi_group(app="web", **kwargs):
    """Create a permission group for the Azubis."""
    _assure_permissions_created()

    azubi_group, _ = Group.objects.get_or_create(name=settings.AZUBI_GROUP_NAME)

    codenames = []
    for model_name, actions in settings.AZUBI_PERMISSIONS.items():
        for action in actions:
            codenames.append(get_permission_codename(action, apps.get_model(app, model_name)._meta))

    # NOTE: this will 'fail silently' if no Permission object exists for a given
    # codename. Maybe query each Permission separately with a get() to make sure
    # that the group contains all the expected permissions?
    azubi_permissions = Permission.objects.filter(codename__in=codenames)
    azubi_group.permissions.set(azubi_permissions)
