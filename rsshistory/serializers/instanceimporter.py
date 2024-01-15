import json

from ..models import Domains
from ..controllers import (
    LinkDataController,
    SourceDataController,
    SourceDataController,
    LinkDataBuilder,
    SourceDataBuilder,
)
from ..apps import LinkDatabase
from ..configuration import Configuration
from ..dateutils import DateUtils


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
    def __init__(self, url=None, author=None):
        self.url = url
        self.author = author

    def import_all(self):
        from ..webtools import BasePage

        p = BasePage(self.url)
        instance_text = p.get_contents()
        if not instance_text:
            return

        try:
            json_data = json.loads(instance_text)
        except Exception as E:
            return

        if "links" in json_data:
            self.import_from_links(json_data["links"])

            if len(json_data["links"]) > 0:
                url = self.get_next_page_link()
                importer = InstanceImporter(url, self.author)
                importer.import_all()

        elif "sources" in json_data:
            self.import_from_sources(json_data["sources"])

            if len(json_data["sources"]) > 0:
                url = self.get_next_page_link()
                importer = InstanceImporter(url, self.author)
                importer.import_all()

        elif "link" in json_data:
            self.import_from_link(json_data["link"])

        elif "source" in json_data:
            self.import_from_source(json_data["source"])

    def get_next_page_link(self):
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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

    def import_from_links(self, json_data):
        LinkDatabase.info("Import from links")

        for link_data in json_data:
            self.import_from_link(link_data)

    def import_from_sources(self, json_data):
        LinkDatabase.info("Import from sources")

        for source_data in json_data:
            self.import_from_source(source_data)

    def import_from_link(self, json_data):

        c = Configuration.get_object().config_entry

        clean_data = self.get_clean_entry_data(json_data)

        entries = LinkDataController.objects.filter(link=clean_data["link"])
        if entries.count() == 0:
            # This instance can have their own settings for import, may decide what is
            # accepted and not. Let the builder deal with it
            LinkDatabase.info("Importing link:{}".format(clean_data["link"]))
            LinkDataBuilder(link_data=clean_data)
        else:
            entry = entries[0]
            if clean_data["bookmarked"] and not entry.bookmarked:
                entry.bookmarked = True
            if clean_data["permanent"] and not entry.permanent:
                entry.permanent = True

            entry.save()

            if "tags" in clean_data:
                entry.tag(clean_data["tags"], self.author)

            if "vote" in clean_data:
                if clean_data["vote"] > 0:
                    entry.vote(clean_data["vote"])

    def import_from_source(self, json_data, instance_import = False):
        LinkDatabase.info("Import from source")

        clean_data = SourceDataController.get_clean_data(json_data)

        sources = SourceDataController.objects.filter(url=clean_data["url"])
        if sources.count() == 0:
            clean_data = self.drop_source_instance_internal_data(clean_data)
            if instance_import:
                clean_data["on_hold"] = True
            SourceDataBuilder.add_from_props(clean_data)
        else:
            if instance_import:
                source = sources[0]

                if source.on_hold != (not clean_data["on_hold"]):
                    source.on_hold = not clean_data["on_hold"]

                if source.proxy_location != clean_data["proxy_location"]:
                    source.proxy_location = clean_data["proxy_location"]

                source.save()

    def drop_entry_instance_internal_data(self, clean_data):
        if "domain_obj" in clean_data:
            del clean_data["domain_obj"]
        if "source_obj" in clean_data:
            del clean_data["domain_obj"]
        if "id" in clean_data:
            del clean_data["id"]

        return clean_data

    def drop_source_instance_internal_data(self, clean_data):
        if "dynamic_data" in clean_data:
            del clean_data["dynamic_data"]
        if "id" in clean_data:
            del clean_data["id"]

        return clean_data

    def get_clean_entry_data(self, input_data):
        clean_data = LinkDataController.get_clean_data(input_data)
        clean_data = self.drop_entry_instance_internal_data(clean_data)

        if "date_published" in clean_data:
            clean_data["date_published"] = DateUtils.parse_datetime(clean_data["date_published"])

        return clean_data
