import os
import json
import traceback
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..models import Domains, AppLogging, UserBookmarks, UserTags, UserVotes

from ..controllers import (
    LinkDataController,
    SourceDataController,
    SourceDataController,
    EntryDataBuilder,
    SourceDataBuilder,
    EntryWrapper,
)
from ..apps import LinkDatabase
from ..configuration import Configuration
from .jsonimporter import MapImporter


class InstanceExporter(object):
    def export_link(self, link):
        link_map = {"link": link.get_map_full()}
        return link_map

    def export_links(self, links):
        json_obj = {"links": []}

        for link in links:
            link_map = link.get_map_full()
            json_obj["links"].append(link_map)

        return json_obj

    def export_source(self, source):
        source_map = {"source": source.get_map_full()}
        return source_map

    def export_sources(self, sources):
        json_obj = {"sources": []}

        for source in sources:
            source_map = source.get_map_full()
            json_obj["sources"].append(source_map)

        return json_obj


class InstanceImporter(object):
    def __init__(self, url=None, user=None):
        self.url = url
        self.user = user

    def import_all(self):
        from ..pluginurl import UrlHandler

        u = UrlHandler(self.url)
        instance_text = u.get_contents()
        if not instance_text:
            return

        try:
            json_data = json.loads(instance_text)
        except Exception as E:
            exc_string = traceback.format_exc()
            AppLogging.info(
                "Cannot load JSON:{}\nExc:{}".format(instance_text, exc_string)
            )
            return

        entry_builder = EntryDataBuilder()
        source_builder = SourceDataBuilder()

        if "links" in json_data:
            importer = MapImporter(entry_builder=entry_builder, source_builder = source_builder, user = self.user)
            importer.import_from_links(json_data["links"])

        elif "sources" in json_data:
            importer = MapImporter(entry_builder=entry_builder, source_builder = source_builder, user = self.user)
            print(json_data["sources"])
            importer.import_from_sources(json_data["sources"])

        elif "link" in json_data:
            importer = MapImporter(entry_builder=entry_builder, source_builder = source_builder, user = self.user)
            importer.import_from_link(json_data["link"])

        elif "source" in json_data:
            importer = MapImporter(entry_builder=entry_builder, source_builder = source_builder, user = self.user)
            importer.import_from_source(json_data["source"])

    def get_next_page_link(self):
        parsed_url = urlparse(self.url)
        query_params = parse_qs(parsed_url.query)

        page_param = 0
        if "page" in query_params:
            page_param = query_params["page"][0]

        if page_param is not None:
            try:
                page_param = int(page_param) + 1
            except ValueError:
                page_param = 0
        else:
            page_param = 0

        # Update the 'page' parameter in the query string
        query_params["page"] = [str(page_param)]

        # Construct the new URL
        new_query_string = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=new_query_string))

        return new_url
