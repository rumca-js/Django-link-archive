import os
import re
import traceback
import time

from ..webtools import DomainAwarePage
from ..models import AppLogging
from ..controllers import LinkDataController, BackgroundJobController
from .sourceparseplugin import BaseParsePlugin
from ..apps import LinkDatabase


class DomainParserPlugin(BaseParsePlugin):
    """
    Finds all domains on site
    """

    PLUGIN_NAME = "DomainParserPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_link_valid(self, link):
        return True

    def get_container_elements(self):
        start_processing_time = time.time()

        domains_vec = self.get_domains()
        num_entries = len(domains_vec)

        index = 0
        for link_str in domains_vec:
            objs = LinkDataController.objects.filter(link=link_str)
            if objs.exists():
                continue

            BackgroundJobController.link_add(link_str, source=self.get_source())

        return []
