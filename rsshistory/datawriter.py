"""
TODO most of the underlying converters should be rewritten to support different entries input
and different output (Year, or page ordered directories)
"""

from pathlib import Path

from .dateutils import DateUtils
from .models import DataExport
from .serializers.sourceserializer import SourcesEntriesDataWriter


class DataWriterConfiguration(object):
    def __init__(self, config, export_config, directory=None, date_iso=None):
        """
        @param date date in ISO format
        """
        self.config = config
        self.export_config = export_config
        self.directory = directory
        self.date_iso = date_iso


class BaseDataWriter(object):
    def __init__(self, data_writer_config):
        self.config = data_writer_config.config
        self.export_config = data_writer_config.export_config
        self.directory = data_writer_config.directory
        self.date_iso = data_writer_config.date_iso

    def get_directory(self):
        return (
            self.config.get_export_path()
            / self.export_config.local_path
            / self.directory
        )

    def get_sources_json(self):
        from .controllers import SourceDataController

        sources = SourceDataController.objects.filter(export_to_cms=True)

        from .serializers.converters import ModelCollectionConverter, JsonConverter

        cc = ModelCollectionConverter(sources)
        items = cc.get_map()

        converter = JsonConverter(items)
        converter.set_export_columns(SourceDataController.get_export_names())
        text = converter.export()

        return text

    def get_domains_json(self):
        from .models import Domains

        domains = Domains.objects.all()

        from .serializers.domainexporter import DomainJsonExporter

        exp = DomainJsonExporter()
        return exp.get_text(domains)

    def get_keywords_json(self, day_iso):
        from .models import KeyWords

        from .serializers.keywordexporter import KeywordExporter

        keywords = KeyWords.get_keyword_data()
        if len(keywords) > 0:
            exp = KeywordExporter()
            return exp.get_text(keywords)


class DailyDataWriter(BaseDataWriter):
    def __init__(self, data_writer_config):
        super().__init__(data_writer_config)

    def get_daily_path(self):
        day_iso = self.date_iso
        daily_path = self.get_directory() / self.config.get_daily_data_day_path(day_iso)
        return daily_path

    def write(self):
        daily_path = self.get_daily_path()

        daily_path.mkdir(parents=True, exist_ok=True)

        self.write_entries(daily_path)
        self.write_sources()
        self.write_keywords()

    def write_entries(self, daily_path):
        day_iso = self.date_iso

        # TODO use config switches (enable permanent, bookmark, all switches)

        writer = SourcesEntriesDataWriter(self.config)
        writer.write_for_day(daily_path, day_iso)

    def write_sources(self):
        if self.export_config.export_sources:
            text = self.get_sources_json()
            file_name = self.get_directory() / self.config.get_sources_file_name()
            file_name.write_text(text)

    def write_keywords(self):
        day_iso = self.date_iso
        daily_path = self.get_daily_path()

        text = self.get_keywords_json(day_iso)
        if text:
            file_name = daily_path / self.config.get_keywords_file_name()
            file_name.write_text(text)


class YearDataWriter(BaseDataWriter):
    def __init__(self, data_writer_config):
        super().__init__(data_writer_config)

    def write(self):
        conf = self.config.config_entry

        self.get_directory().mkdir(parents=True, exist_ok=True)

        self.write_entries()
        self.write_sources()

    def write_entries(self):
        from .serializers.bookmarksexporter import BookmarksBigExporter

        if self.export_config.export_entries_bookmarks:
            exporter = BookmarksBigExporter(self.config)
            exporter.export(self.get_directory())

            # TODO implement permanent write

    def write_sources(self):
        if self.export_config.export_sources:
            text = self.get_sources_json()
            file_name = self.get_directory() / self.config.get_sources_file_name()
            file_name.write_text(text)


class NoTimeDataWriter(BaseDataWriter):
    def __init__(self, data_writer_config):
        super().__init__(data_writer_config)

    def write(self):
        conf = self.config.config_entry

        self.get_directory().mkdir(parents=True, exist_ok=True)

        self.write_entries()
        self.write_sources()

    def write_entries(self):
        from .serializers.permanententriesexporter import PermanentEntriesExporter

        if self.export_config.export_entries_permanents:
            exporter = PermanentEntriesExporter(self.config)
            exporter.export("permanents", self.get_directory())

            # TODO implement bookmark writing

    def write_sources(self):
        if self.export_config.export_sources:
            text = self.get_sources_json()
            file_name = self.get_directory() / self.config.get_sources_file_name()
            file_name.write_text(text)


class DataWriter(object):
    def get(data_writer_configuration):
        # fmt: off

        if data_writer_configuration.export_config.export_data == DataExport.EXPORT_DAILY_DATA:
            return DailyDataWriter(data_writer_configuration)
        elif data_writer_configuration.export_config.export_data == DataExport.EXPORT_YEAR_DATA:
            return YearDataWriter(data_writer_configuration)
        elif data_writer_configuration.export_config.export_data == DataExport.EXPORT_NOTIME_DATA:
            return NoTimeDataWriter(data_writer_configuration)
        else:
            raise NotImplementedError("Not implemented")
        # fmt: on
