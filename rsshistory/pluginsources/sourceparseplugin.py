import traceback
import re
import os
import time

from .sourcegenericplugin import SourceGenericPlugin
from ..models import PersistentInfo
from ..controllers import LinkDataController, LinkDataHyperController
from ..webtools import BasePage, HtmlPage
from ..apps import LinkDatabase


class BaseParsePlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseParsePlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    # def get_address(self):
    #    return self.get_source().get_domain()

    def is_link_valid(self, address):
        source = self.get_source()

        if not self.is_link_valid_domain(address):
            return False

        if not address.startswith(source.url):
            return False

        p = BasePage(address)
        ext = p.get_page_ext()

        if ext == "html" or ext == "htm" or ext == "":
            return True

        return False

    def get_link_data(self, source, link):
        from ..dateutils import DateUtils

        output_map = {}
        return LinkDataHyperController.get_htmlpage_props(link, output_map, source)

    def get_link_props(self):
        try:
            start_processing_time = time.time()

            links_str_vec = self.get_links()
            num_entries = len(links_str_vec)

            for index, link_str in enumerate(links_str_vec):
                if not self.is_link_valid(link_str):
                    continue

                objs = LinkDataController.objects.filter(link=link_str)
                if objs.exists():
                    continue

                link_props = self.get_link_data(self.get_source(), link_str)

                print(
                    "[{}] Processing parsing link {}:[{}/{}]".format(
                        LinkDatabase.name, link_str, index, num_entries
                    )
                )

                yield link_props

                # if 10 minutes passed
                if time.time() - start_processing_time >= 60 * 10:
                    break

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "Source:{}; Exc:{}\n{}".format(self.source_id, str(e), error_text)
            )
