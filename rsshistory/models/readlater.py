from django.db import models
from django.conf import settings

from ..apps import LinkDatabase
from .entries import LinkDataModel


class ReadLater(models.Model):
    entry = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="read_later",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_read_later",
        null=True,
    )
