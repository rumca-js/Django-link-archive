import traceback
import re

from .sourcegenericplugin import SourceGenericPlugin
from ..models import PersistentInfo, LinkDataModel
from ..controllers import LinkDataController


class BaseParsePlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseParsePlugin"

    def __init__(self, source):
        super().__init__(source)

    def get_address(self):
        return self.source.get_domain()

    def is_link_valid(self, address):
        print("Address:{} link:{}".format(self.source.url, address))

        if not self.is_link_valid_domain(address):
            return False

        if not address.startswith(self.source.url):
            return

        if (
            address.endswith(".html")
            or address.endswith(".htm")
            or address.endswith("/")
        ):
            search_pattern = self.source.get_domain()

            if re.search(search_pattern, address):
                return True
        return False

    def get_link_data(self, source, link):
        from ..webtools import Page
        from ..dateutils import DateUtils

        output_map = {}

        link_ob = Page(link)

        title = link_ob.get_title()
        if not title:
            return output_map

        output_map["link"] = link
        output_map["title"] = title
        output_map["description"] = title
        output_map["source"] = source.url
        output_map["published"] = DateUtils.get_datetime_now_utc()
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

                props.append(self.get_link_data(self.source, link_str))

            return props
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "Source:{} {}; Exc:{}\n{}".format(
                    source.url, source.title, str(e), error_text
                )
            )
