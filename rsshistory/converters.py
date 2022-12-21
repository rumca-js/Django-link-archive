
import logging


class SourceConverter(object):
    def __init__(self, row_data):
        self.process_string(row_data)

    def process_string(self, row_data):
         delimiter = ";"
         link_info = row_data.split(delimiter)

         self.url = link_info[0]
         self.title = link_info[1]
         self.category = link_info[2]
         self.subcategory = link_info[3]
         self.date_fetched = link_info[4]
         self.dead = link_info[5]
         self.export_to_cms = link_info[6]
         self.remove_after_days = link_info[7]
         self.language = link_info[8]

    def get_text(self):
        return "{0};{1};{2};{3};{4};{5};{6};{7};{8}".format(self.url,
                                                    self.title,
                                                    self.category,
                                                    self.subcategory,
                                                    self.date_fetched,
                                                    self.dead,
                                                    self.export_to_cms,
                                                    self.remove_after_days,
                                                    self.language)


class SourcesConverter(object):

    def __init__(self, data = None):
        if data:
            self.process_string(data)

    def process_string(self, data):
        delimiter = "\n"
        links = data.split(delimiter)
        self.sources = []

        for link_row in links:
             link_row = link_row.replace("\r", "")
             link = SourceConverter(link_row)
             self.sources.append(link)

    def set_sources(self, sources):
        self.sources = sources

    def get_text(self):
        summary_text = ""
        for source in self.sources:
            data = SourceConverter.get_text(source)
            summary_text += data + "\n"
        return summary_text

    def get_export_path(self):
       entries_dir = self._cfg.get_highlights_path()
       export_path = entries_dir

       if not export_path.exists():
           export_path.mkdir()

       return export_path

    def export(self, config):
        self._cfg = config
        text = self.get_text()

        export_path = self.get_export_path()

        file_name = export_path / ("sources.csv")
        #log.info("writing json: " + file_name.as_posix() )
        file_name.write_text(self.get_text())


class EntryConverter(object):
    def __init__(self, row_data = None):
        if row_data:
            self.process_string(row_data)
        self.with_description = True
        self.entry = None

    def process_string(self, row_data):
        from urllib.parse import urlparse
        delimiter = ";"
        link_info = row_data.split(delimiter)

        self.title = ""
        self.date_published = datetime.now
        self.source = ""
        self.persistent = True
        self.description = ""

        self.link = link_info[0]

        if len(link_info) > 1:
            if len(link_info[1].strip()) > 0:
                self.title = link_info[1]
        else:
            from .webtools import Page
            parser = Page(self.link)
            self.title = parser.get_title()

        if len(link_info) > 2:
            if len(link_info[2].strip()) > 0:
                self.date_published = link_info[2]

        if len(link_info) > 3:
            if len(link_info[3].strip()) > 0:
                self.source = link_info[3]
            else:
                self.source = urlparse(self.link).netloc
        else:
            if len(self.link) > 4:
                self.source = urlparse(self.link).netloc

        if len(link_info) > 4:
            self.persistent = link_info[4] == "True"

        if len(link_info) > 5:
            if len(link_info[5].strip()) > 0:
                self.description = link_info[5]

    def get_map(self):
        data = {}
        data['source'] = self.source
        data['link'] = self.link
        data['title'] = self.title
        data['date_published'] = str(self.date_published)
        data['description'] = self.description
        data['persistent'] = self.persistent
        data['language'] = self.language

        return data

    def set_entry(self, entry):
        self.entry = entry
        self.source = entry.source
        self.link = entry.link
        self.title = entry.title
        self.date_published = entry.date_published
        self.description = entry.description
        self.persistent = entry.persistent
        self.language = entry.language

    def get_csv_text(self):
        return "{0};{1};{2};{3};{4};{5}".format(self.link, self.source, self.persistent, self.title, self.date_published, self.description)

    def get_clean_text(self):
        return "{0}\n{1}\n{2}\n{3}\n{4}\n{5}\n".format(self.source, self.self, self.title, self.date_published, self.persistent, self.description)

    def get_md_text(self):
        tags = ""
        if self.entry:
            if self.entry.language == None:
                self.entry.update_language()

            tags = self.entry.get_tag_string()

        result_string = ""
        result_string += "## {0}\n".format(self.title)
        result_string += " - [{0}]({0})\n".format(self.link)
        result_string += " - RSS feed: {0}\n".format(self.source)
        result_string += " - date published: {0}\n".format(self.date_published)
        if tags != "" and tags != None:
            result_string += " - tags: {0}\n".format(tags)
        result_string += "\n"
        if self.with_description:
            result_string += "{0}\n".format(self.description)

        return result_string

    def get_rss_text(self):
        return "<item><title>![CDATA[{0}]]</title><description>![CDATA[{1}]]</description><pubDate>{2}</pubDate><link>{3}</link></item><guid isPermaLink=\"false\">{4}</guid>".format(self.title, self.description, self.date_published, self.link, self.link)


class EntriesConverter(object):

    def __init__(self, data = None):
        self.with_description = True
        self._source = {}

        if data:
            self.process_string(data)

    def process_string(self, data):
        delimiter = "\n"
        entries = data.split(delimiter)
        self.entries = []

        for entry_row in entries:
             entry_row = entry_row.replace("\r", "")
             entry = EntryConverter(entry_row)
             self.entries.append(entry)

    def set_entries(self, entries):
        self.entries = entries

    def set_source(self, source):
        self._source['source url'] = source.url
        self._source['source title'] = source.title

    def set_source_url(self, source_url):
        self._source['source url'] = source_url
        self._source['source title'] = source_url

    def get_json(self):
        output_data = {}
        output_data['entries'] = []

        if 'source url' in self._source:
            output_data['source url'] = self._source['source url']
        if 'source title' in self._source:
            output_data['source title'] = self._source['source title']

        for entry in self.entries:
            entry_data = EntryConverter.get_map(entry)
            output_data['entries'].append(entry_data)
            
        import json
        return json.dumps(output_data)

    def get_csv_text(self):
        output_data = []
        for entry in self.entries:
            entry_data = EntryConverter.get_csv_text(entry)
            output_data.append(entry_data)
            
        return "\n".join(output_data)

    def get_clean_text(self):
        output_data = []
        for entry in self.entries:
            entry_data = EntryConverter.get_clean_text(entry)
            output_data.append(entry_data)
            
        return "\n".join(output_data)

    def get_md_text(self):
        output_data = []
        for entry in self.entries:
            ec = EntryConverter()
            ec.with_description = self.with_description
            ec.set_entry(entry)
            entry_data = ec.get_md_text()
            output_data.append(entry_data)
            
        return "\n".join(output_data)

    def get_rss_text(self):
        output_data = []
        for entry in self.entries:
            ec = EntryConverter()
            ec.with_description = self.with_description
            ec.set_entry(entry)
            entry_data = ec.get_rss_text()
            output_data.append(entry_data)
            
        return "\n".join(output_data)


class EntriesExporter(object):

    def __init__(self, config, entries):
        self._entries = entries
        self._cfg = config

    def export_entries(self, source_url, export_file_name = "default", entries_dir = None, with_description = True):
        if len(self._entries) == 0:
            return

        e_converter = EntriesConverter()
        e_converter.set_entries(self._entries)
        e_converter.with_description = with_description

        from .models import RssSourceDataModel
        sources = RssSourceDataModel.objects.filter(url = source_url)
        if sources.exists():
            e_converter.set_source(sources[0])
            source_title = sources[0].title
        else:
            e_converter.set_source_url(source_url)
            source_title = source_url

        entries_dir = self._cfg.get_export_path() / entries_dir
        export_path = entries_dir

        if not export_path.exists():
            export_path.mkdir(parents = True)

        log = logging.getLogger(self._cfg.app_name)

        file_name = export_path / (export_file_name + "_entries.json")
        #log.info("writing json: " + file_name.as_posix() )
        file_name.write_text(e_converter.get_json())

        if sources.exists():
            source = sources[0]
            md_text = "# Source {0}, Source URL:{1}, Source language: {2}\n\n".format(source.title,
                     source.url,
                     source.language)

            md_text = md_text + e_converter.get_md_text()
        else:
            md_text = "# Source URL:{0}, Source language: {1}\n\n".format(source_url,
                    self._entries[0].language)

            md_text = md_text + e_converter.get_md_text()

        file_name = export_path / (export_file_name + "_entries.md")
        #log.info("writing md: " + file_name.as_posix() )
        file_name.write_bytes(md_text.encode("utf-8", "ingnore"))

        #log.info("writing done")

    def export_all_entries(self, with_description = True):
        if len(self._entries) == 0:
            return

        e_converter = EntriesConverter()
        e_converter.set_entries(self._entries)
        e_converter.with_description = with_description

        entries_dir = self._cfg.get_export_path() / self._cfg.get_date_file_name()
        export_path = entries_dir

        if not export_path.exists():
            export_path.mkdir()

        log = logging.getLogger(self._cfg.app_name)

        file_name = export_path / ("all_entries.json")
        #log.info("writing json: " + file_name.as_posix() )
        file_name.write_text(e_converter.get_json())

        md_text = e_converter.get_md_text()

        file_name = export_path / ("all_entries.md")
        #log.info("writing md: " + file_name.as_posix() )
        file_name.write_bytes(md_text.encode("utf-8", "ingnore"))

        #log.info("writing done")
