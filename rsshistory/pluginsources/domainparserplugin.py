import os
import re
import traceback

from ..webtools import Page
from ..models import PersistentInfo
from ..controllers import LinkDataController
from .sourceparseplugin import BaseParsePlugin


class DomainParserPlugin(BaseParsePlugin):
    """
    Created for https://nownownow.com/
    """
    PLUGIN_NAME = "DomainParserPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_link_props(self):
        try:
            props = []

            domains_vec = self.get_domains()
            num_entries = len(domains_vec)

            for link_str in domains_vec:
                p = Page(link_str)
                if p.is_valid() == False:
                    continue

                print("Adding domain: {}".format(link_str))

                objs = LinkDataController.objects.filter(link=link_str)
                if objs.exists():
                    continue

                props.append(self.get_link_data(self.get_source(), link_str))

            return props
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "Source:{}; Exc:{}\n{}".format(self.source_id, str(e), error_text)
            )
