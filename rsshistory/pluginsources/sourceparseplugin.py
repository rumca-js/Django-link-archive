import traceback
import re
import os

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
        if not title:
            return output_map

        output_map["link"] = link
        output_map["title"] = title
        output_map["description"] = title
        output_map["source"] = source.url
        output_map["date_published"] = DateUtils.get_datetime_now_utc()
        output_map["language"] = source.language
        output_map["thumbnail"] = None
        return output_map

    def get_link_props(self):
        try:
            props = []

            links_str_vec = self.get_links()
            num_entries = len(links_str_vec)

            for link_str in links_str_vec:
                if not self.is_link_valid(link_str):
                    continue

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
