from django.conf import settings
from django.db import models
from django_softdelete.models import SoftDeleteModel


class PermsTestModel(models.Model):
    pass


class SoftDeleteTestModel(SoftDeleteModel):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
