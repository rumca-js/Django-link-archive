import traceback
from dateutil import parser

from .sourcegenericplugin import SourceGenericPlugin
from ..models import PersistentInfo, BaseLinkDataController


class BaseRssPlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source):
        super().__init__(source)
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_link_props(self):
        try:
            from ..webtools import RssPropertyReader

            reader = RssPropertyReader(self.source.url)
            all_props = reader.parse_and_process()

            if len(all_props) == 0:
                PersistentInfo.error(
                    "Source:{0} {1}; Source has no data".format(
                        self.source.url, self.source.title
                    )
                )

            result = []

            for prop in all_props:
                prop = self.enhance(prop)
                if self.is_link_ok_to_add(prop):
                    result.append(prop)
            return result

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "BaseRssPlugin:get_link_props: Source:{} {}; Exc:{}\n{}".format(
                    self.source.url, self.source.title, str(e), error_text
                )
            )
            return []

    def is_link_ok_to_add(self, props):
        try:
            from ..controllers import LinkDataController

            is_archive = BaseLinkDataController.is_archive_by_date(
                props["date_published"]
            )
            if is_archive:
                return False

            objs = LinkDataController.objects.filter(link=props["link"])
            # print("Adding link {} {}".format(props["link"], props["title"]))

            if not objs.exists():
                if "title" not in props:
                    PersistentInfo.error(
                        "Link:{}; Title:{} missing published field".format(
                            props["link"],
                            props["title"],
                        )
                    )
                    return False

                if not self.is_link_valid(props["link"]):
                    return False

                # print("Link is valid {}".format(props["link"]))

                if "date_published" not in props:
                    PersistentInfo.error(
                        "Link:{}; Title:{} missing published field".format(
                            props["link"],
                            props["title"],
                        )
                    )
                    return False

                # print("Link - checking page {}".format(props["link"]))

                from ..webtools import Page

                p = Page(props["link"])
                if p.is_youtube():
                    print("Link - it is youtube {}".format(props["link"]))
                    from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

                    handler = YouTubeLinkHandler(props["link"])
                    handler.download_details()
                    print(
                        "Link - it is youtube {}, valid:{}".format(
                            props["link"], handler.is_valid()
                        )
                    )
                    if not handler.is_valid():
                        return False

                return True

            return False

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Link:{}; Title:{}; Exc:{}\n{}".format(
                    props["link"],
                    props["title"],
                    str(e),
                    error_text,
                )
            )

            return None

    def enhance(self, prop):
        prop["description"] = prop["description"][
            : BaseLinkDataController.get_description_length() - 2
        ]

        if prop["link"].endswith("/"):
            prop["link"] = prop["link"][:-1]

        prop["source"] = self.source.url
        prop["language"] = self.source.language
        prop["artist"] = self.source.title
        prop["album"] = self.source.title

        return prop
