"""
TODO most of the underlying converters should be rewritten to support different entries input
and different output (Year, or page ordered directories)
"""

from pathlib import Path
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from .models import DataExport, AppLogging
from .models import KeyWords
from .controllers import DomainsController

from .serializers import (
    SourceSerializerWrapper,
    DomainJsonExporter,
    KeywordExporter,
    EntryYearDataMainExporter,
    EntryNoTimeDataMainExporter,
    EntryDailyDataMainExporter,
)


class DataWriterConfiguration(object):
    def __init__(self, config, export_config, directory, date_iso=None):
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
        self.data_writer_config = data_writer_config

    def get_directory(self):
        return self.directory

    def get_domains_json(self):
        domains = DomainsController.objects.all()

        exp = DomainJsonExporter()
        return exp.get_text(domains)

    def get_keywords_json(self, day_iso):
        keywords = KeyWords.get_keyword_data()
        if len(keywords) > 0:
            exp = KeywordExporter()
            return exp.get_text(keywords)

    def get_export_user(self):
        name = self.export_config.db_user
        user_objects = User.objects.filter(username=name)
        if user_objects.count() > 0:
            return user_objects[0]


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
        if not self.export_config.export_entries:
            return

        day_iso = self.date_iso
        writer = EntryDailyDataMainExporter(self.data_writer_config)
        writer.write_for_day(daily_path, day_iso)

    def write_sources(self):
        if not self.export_config.export_sources:
            return

        serializer = SourceSerializerWrapper()
        serializer.export(self.get_directory(), self.config.get_sources_file_name())

    def write_keywords(self):
        if not self.export_config.export_keywords:
            return

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
        if not self.export_config.export_entries:
            return

        exporter = EntryYearDataMainExporter(
            self.data_writer_config, user=self.get_export_user()
        )
        exporter.export(self.get_directory())

    def write_sources(self):
        if not self.export_config.export_sources:
            return

        serializer = SourceSerializerWrapper()
        serializer.export(self.get_directory(), self.config.get_sources_file_name())


class NoTimeDataWriter(BaseDataWriter):
    def __init__(self, data_writer_config):
        super().__init__(data_writer_config)

    def write(self):
        conf = self.config.config_entry

        self.get_directory().mkdir(parents=True, exist_ok=True)

        self.write_entries()
        self.write_sources()

    def write_entries(self):
        if not self.export_config.export_entries:
            return

        exporter = EntryNoTimeDataMainExporter(self.data_writer_config)
        exporter.export("permanents", self.get_directory())

    def write_sources(self):
        if not self.export_config.export_sources:
            return

        serializer = SourceSerializerWrapper()
        serializer.export(self.get_directory(), self.config.get_sources_file_name())


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
