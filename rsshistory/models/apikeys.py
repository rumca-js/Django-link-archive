from django.conf import settings
from django.db import models

from ..apps import LinkDatabase

class ApiKeys(models.Model):
    key = models.CharField(max_length=1000, null=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_apikeys",
        null=True,
    )
