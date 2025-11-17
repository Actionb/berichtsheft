from django.apps import apps


def _get_soft_delete_models(app_label="web"):
    for model in apps.get_app_config(app_label).get_models():
        if hasattr(model, "deleted_objects"):
            yield model


def collect_deleted_objects(user):
    """
    Collect all soft-deleted items for the current user

    Returns a list of deleted_objects querysets for every model.
    """
    objects = []
    for model in _get_soft_delete_models(app_label="web"):
        queryset = model.deleted_objects.filter(user=user)
        if queryset.exists():
            objects.append(queryset)
    return objects
