"""
Security is a made up word.
"""

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models

from ..apps import LinkDatabase


FERNET_KEY = settings.FERNET_KEY
fernet = Fernet(FERNET_KEY)


class Credentials(models.Model):
    """
    You can define access to multiple sources here
    """

    name = models.CharField(max_length=1000, blank=True)  # github etc
    credential_type = models.CharField(
        max_length=1000, blank=True
    )  # refresh token, auth token, etc.
    username = models.CharField(max_length=1000, blank=True)
    password = models.CharField(max_length=1000, blank=True)
    secret = models.CharField(max_length=1000, blank=True)
    token = models.CharField(max_length=1000, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_credentials",
        null=True,
        blank=True,
        help_text="Owner of credentials",
    )

    class Meta:
        ordering = ["user"]

    def encrypt(self):
        """Still the better way than Facebook plaintext."""
        if self.secret:
            self.secret = fernet.encrypt(self.secret.encode()).decode()
        if self.token:
            self.token = fernet.encrypt(self.token.encode()).decode()
        if self.password:
            self.password = fernet.encrypt(self.password.encode()).decode()

    def decrypt(self):
        if self.secret:
            self.secret = fernet.decrypt(self.secret.encode()).decode()
        if self.token:
            self.token = fernet.decrypt(self.token.encode()).decode()
        if self.password:
            self.password = fernet.decrypt(self.password.encode()).decode()
        return None

    def __str__(self):
        return "{}/{}".format(self.name, self.credential_type)
