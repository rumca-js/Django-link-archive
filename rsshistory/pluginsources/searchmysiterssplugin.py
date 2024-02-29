import os
import re
from django.contrib.auth.models import User

from ..models import UserTags
from ..configuration import Configuration
from .sourcerssplugin import BaseRssPlugin


class SearchMySiteRSSPlugin(BaseRssPlugin):
    """
    Created for https://searmysite.net/
    """

    PLUGIN_NAME = "SearchMySiteRSSPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def on_added_entry(self, entry):
        c = Configuration.get_object()

        admin_user = User.objects.get(is_superuser=True)

        UserTags.set_tag(entry, "personal", admin_user)
