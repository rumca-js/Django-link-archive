
import logging
import traceback
from ..models import PersistentInfo


class ModelCollectionConverter(object):

    def __init__(self, items):
        self.items = items

    def get_map(self):
        result = []
        for item in self.items:
            result.append(item.get_map())

        return result

    def get_map_full(self):
        result = []
        for item in self.items:
            result.append(item.get_map_full())

        return result


class ItemConverterFabric(object):

    def __init__(self, items):
        self.export_columns_all = True
        self.export_columns = []
        self.items = items

    def set_export_columns(self, export_columns):
        self.export_columns_all = False
        self.export_columns = export_columns

    def get_export_columns(self):
        if self.export_columns_all:
            keys = []
            for item in self.items:
                keys.append(item)

            self.export_columns = keys
        return self.export_columns

    def get_filtered_columns(self):
        if self.export_columns_all:
            return self.items

        result = []
        for item in self.items:
            result_dict = {}
            for use_column in self.export_columns:
                if use_column in item:
                    result_dict[use_column] = item[use_column]

            result.append(result_dict)

        return result

    def export(self):
        raise NotImplemented("Not implemented")

    def from_text(self, text):
        raise NotImplemented("Not implemented")


class JsonConverter(ItemConverterFabric):

    def __init__(self, items):
        super().__init__(items)

    def export(self):
        item_data = self.get_filtered_columns()

        import json
        return json.dumps(item_data) 

    def from_text(self, text):
        import json
        return json.loads(text) 


import csv
from io import StringIO

class CsvConverter(ItemConverterFabric):

    def __init__(self, items):
        super().__init__(items)
        csv.register_dialect('semi', delimiter=';', quoting=csv.QUOTE_NONE)

    def export(self):
        # TODO
        item_data = self.get_filtered_columns()

        fieldnames = self.get_export_columns()
        with StringIO() as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, dialect = 'semi')

            writer.writeheader()

            for item in item_data:
                writer.writerow(item)

            fh.seek(0)
            return fh.read()

    def from_text(self, text):
        items = []
        with StringIO(text) as fh:
            reader = csv.DictReader(fh, dialect = 'semi')
            for row in reader:
                items.append(row)

        return items


from string import Template

class MarkDownConverter(ItemConverterFabric):

    def __init__(self, items, item_template):
        super().__init__(items)
        self.item_template = item_template

    def export(self):
        result = ""

        items_data = self.get_filtered_columns()
        for item in items_data:
            item_data = self.use_template(item)
            result += item_data + "\n"

        return result

    def use_template(self, map_data):
        try:
            t = Template(self.item_template)
            return t.safe_substitute(map_data)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Template exception {0} {1} {2} {3}".format(self.item_template, str(map_data), str(e), error_text))
        return ""


class RssConverter(MarkDownConverter):

    def __init__(self, items, item_template = None):
        if item_template == None:
            super().__init__(items, self.get_template())
        else:
            super().__init__(items, item_template)

    def get_template(self):
        return "<item><title>![CDATA[$title]]</title><description>![CDATA[$description]]</description><pubDate>$date_published</pubDate><link>$link</link></item><guid isPermaLink=\"false\">$link</guid>"


class MarkDownSourceConverter(object):
    def __init__(self, source, item_template):
        self.item_template = item_template
        self.source = source

    def export(self):
        map_data = self.source.get_map()
        return self.use_template(map_data)

    def use_template(self, map_data):
        try:
            t = Template(self.item_template)
            return t.safe_substitute(map_data)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Template exception {0} {1} {2} {3}".format(self.item_template, str(map_data), str(e), error_text))
        return ""
