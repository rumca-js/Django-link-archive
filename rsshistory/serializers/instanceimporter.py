import json

from ..controllers import LinkDataController, SourceDataController


class InstanceImporter(object):
    def __init__(self, url):
        self.url = url

    def import_all(self):
        from ..webtools import Page
        p = Page(self.url)
        instance_text = p.get_contents()

        json_data = json.loads(instance_text)

        if 'links' in json_data:
            self.import_from_links(json_data['links'])

        if 'sources' in json_data:
            self.import_from_sources(json_data['sources'])

        if 'link' in json_data:
            self.import_from_link(json_data['link'])

        if 'source' in json_data:
            self.import_from_source(json_data['source'])

    def import_from_links(self, json_data):
        print("Import from links")

        for link_data in json_data:
            LinkDataController.objects.create(**link_data)

    def import_from_sources(self, json_data):
        print("Import from sources")

        for source_data in json_data:
            SourceDataController.objects.create(**source_data)

    def import_from_link(self, json_data):
        print("Import from link")

        LinkDataController.objects.create(**json_data)

    def import_from_source(self, json_data):
        print("Import from source")

        SourceDataController.objects.create(**json_data)
