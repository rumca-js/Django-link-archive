import traceback
from dateutil import parser
import json

from ..serializers import MapImporter

from ..controllers import (
    SourceDataBuilder,
    EntryDataBuilder,
)
from ..models import AppLogging
from ..apps import LinkDatabase
from ..pluginurl import UrlHandlerEx

from ..configuration import Configuration
from ..serializers.instanceimporter import InstanceImporter

from .sourcegenericplugin import SourceGenericPlugin


class BaseSourceJsonPlugin(SourceGenericPlugin):
    """
    This plugin allows to import source from a different instance, regularly, automatically.

    Address should be to source json https://renegat0x0.ddns.net/apps/rsshistory/source-json/284
    """

    PLUGIN_NAME = "BaseSourceJsonPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_entries(self):
        json = self.get_json()
        if not json:
            return []

        if "source" in json:
            self.get_links_from_source(json["source"])

        if "links" in json:
            self.get_links_from_links(json["links"])

        if "sources" in json:
            sources = self.get_all_sources(json["sources"])
            self.get_links_from_sources(sources)

        return []

    def get_json(self, url=None):
        if url is None:
            address = self.get_address()
            contents = self.get_contents()
        else:
            address = url
            contents = UrlHandlerEx(address).get_contents()

        if not contents:
            AppLogging.error("Could not load JSON {} - no data".format(address))

        try:
            j = json.loads(contents)
            return j

        except ValueError as E:
            AppLogging.exc(E, "Could not load JSON {}".format(address))

    def get_links_from_source(self, source_json):
        if not source_json["enabled"]:
            return

        c = Configuration.get_object().config_entry

        for index, prop in enumerate(self.get_entries_for_source(source_json)):
            if prop["dead"]:
                continue

            entry_builder = EntryDataBuilder()
            source_builder = SourceDataBuilder()
            # TODO this might not work
            user = c.admin_user
            i = MapImporter(
                entry_builder=entry_builder, source_builder=source_builder, user=user
            )

            i.import_from_link(prop)

            ## we do not return any found links, because instance importer imports them directly

    def get_all_sources(self, sources):
        address = self.get_address()

        while True:
            i = InstanceImporter(address)
            address = i.get_next_page_link()
            print("Obtaining address {}".format(address))

            if not address:
                return sources

            json = self.get_json(address)

            if not json or len(json) == 0:
                return sources

            print("Obtained json {}".format(json))

            if "sources" in json:
                new_sources = json["sources"]

                if len(new_sources) == 0:
                    return sources

                sources.extend(new_sources)
            else:
                AppLogging.error("No sources")
                return sources

    def get_links_from_sources(self, sources):
        c = Configuration.get_object().config_entry

        for index, source_prop in enumerate(sources):
            if not source_prop["enabled"]:
                continue

            i = InstanceImporter()
            # TODO use configured author
            i.author = c.admin_user

            source_prop["proxy_location"] = self.get_source_url(source_prop)

            entry_builder = EntryDataBuilder()
            source_builder = SourceDataBuilder()
            # TODO this might not work
            user = c.admin_user
            i = MapImporter(
                entry_builder=entry_builder, source_builder=source_builder, user=user
            )
            i.import_from_source(source_prop)

    def get_links_from_links(self, links_json):
        c = Configuration.get_object().config_entry

        for index, prop in enumerate(links_json):
            if prop["dead"]:
                continue

            entry_builder = EntryDataBuilder()
            source_builder = SourceDataBuilder()
            # TODO this might not work
            user = c.admin_user
            i = MapImporter(
                entry_builder=entry_builder, source_builder=source_builder, user=user
            )
            i.import_from_link(prop)

            ## we do not return any found links, because instance importer imports them directly

    def get_instance_root(self):
        """
        @example source URL is https://renegat0x0.ddns.net/apps/rsshistory/source/284/
        """
        address = self.get_address()
        wh = address.rfind("source")
        if wh >= 0:
            address = address[: wh - 1]

        if address.endswith("/"):
            address = address[:-1]

        return address

    def get_entries_for_source(self, source_json):
        """
        TODO we should be using source url, not title?
        @return list of entries JSONs
        """
        recent_url = self.get_entries_recent_url(source_json)
        print("Getting recent link list from url:{}".format(recent_url))
        recent_entries_list_contents = UrlHandlerEx(recent_url).get_contents()

        if not recent_entries_list_contents:
            AppLogging.error(
                "Could not obtain JSON for recent entries: {}".format(recent_url)
            )
            return

        recent_entries_json = None
        try:
            recent_entries_json = json.loads(recent_entries_list_contents)
        except ValueError as E:
            AppLogging.exc(
                E,
                "Could not read recent entries JSON {}".format(
                    recent_entries_list_contents
                ),
            )

        if recent_entries_json:
            if "links" not in recent_entries_json:
                return

            for recent_entry in recent_entries_json["links"]:
                yield recent_entry

    def get_entries_recent_url(self, source_json):
        path = (
            self.get_instance_root()
            + "/entries-json/?query_type=recent&source_title={}".format(
                source_json["title"]
            )
        )
        return str(path)

    def get_source_url(self, source_json):
        path = self.get_instance_root() + "/source-json/{}".format(source_json["id"])
        return str(path)
