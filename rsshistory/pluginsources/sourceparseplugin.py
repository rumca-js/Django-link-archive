import traceback
import re
import os
import time

from .sourcegenericplugin import SourceGenericPlugin
from ..models import PersistentInfo
from ..controllers import LinkDataController
from ..webtools import BasePage, HtmlPage


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

        link_ob = HtmlPage(link)

        title = link_ob.get_title()
        description = link_ob.get_description()
        if description is None:
            description = title

        language = link_ob.get_language()
        if not language:
            language = source.language

        output_map["link"] = link
        output_map["title"] = title
        output_map["description"] = description
        output_map["source"] = source.url
        output_map["date_published"] = DateUtils.get_datetime_now_utc()
        output_map["language"] = language
        output_map["thumbnail"] = link_ob.get_image()

        return output_map

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

                print("[{}] Processing parsing link {}:[{}/{}]".format(LinkDatabase.name, link_str, index, num_entries))

                yield link_props

                # if 10 minutes passed
                if time.time() - start_processing_time >= 60 * 10:
                    break

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "Source:{}; Exc:{}\n{}".format(self.source_id, str(e), error_text)
            )
