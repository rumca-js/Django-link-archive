from .dateutils import DateUtils


class SourceEntriesDataWriter(object):

    def __init__(self, config, source_url):
        self._cfg = config
        self.source_url = source_url

    def write_for_day(self, day_iso):
        from .models import RssSourceEntryDataModel
        from .serializers.entriesexporter import EntriesExporter

        date_range = DateUtils.get_range4day(day_iso)
        entries = RssSourceEntryDataModel.objects.filter(source = self.source_url, date_published__range=date_range)

        clean_url = self._cfg.get_url_clean_name(self.source_url)

        ex = EntriesExporter(self._cfg, entries)
        ex.export_entries(self.source_url, clean_url, self._cfg.get_daily_data_path(day_iso))


class SourcesEntriesDataWriter(object):

    def __init__(self, config):
        self._cfg = config

    def write_for_day(self, day_iso):
        """ We do not want to provide for each day cumulative view. Users may want to select which 'streams' are selected individually '"""
        from .models import RssSourceDataModel, RssSourceEntryDataModel

        date_range = DateUtils.get_range4day(day_iso)

        # some entries might not have source in the database - added manually.
        # first capture entries, then check if has export to CMS.
        # if entry does not have source, it was added manually and is subject for export

        entries = RssSourceEntryDataModel.objects.filter(date_published__range = date_range)
        sources_urls = set(entries.values_list('source', flat=True).distinct())

        for source_url in sources_urls:
            source_objs = RssSourceDataModel.objects.filter(url = source_url)
            if source_objs.exists() and not source_objs[0].export_to_cms:
               continue

            writer = SourceEntriesDataWriter(self._cfg, source_url)
            writer.write_for_day(day_iso)


class DataWriter(object):
    def __init__(self, config):
        self._cfg = config

    def write_daily_data(self, day_iso):
        writer = SourcesEntriesDataWriter(self._cfg)
        writer.write_for_day(day_iso)

    def write_bookmarks(self):
        from .serializers.bookmarksexporter import BookmarksBigExporter

        exporter = BookmarksBigExporter(self._cfg)
        exporter.export()

    def write_sources(self):
        from .models import RssSourceDataModel

        sources = RssSourceDataModel.objects.filter(export_to_cms = True)

        from .serializers.converters import ModelCollectionConverter, JsonConverter

        cc = ModelCollectionConverter(sources)
        items = cc.get_map()

        converter = JsonConverter(items)
        converter.set_export_columns(['url', 'title', 'category', 'subcategory', 'dead', 'export_to_cms', 'remove_after_days', 'language', 'favicon', 'on_hold'])
        text = converter.export()

        self._cfg.get_bookmarks_path().mkdir(parents=True, exist_ok = True)
        self._cfg.get_daily_data_path().mkdir(parents=True, exist_ok = True)

        file_name = self._cfg.get_bookmarks_path() / self._cfg.get_sources_file_name()
        file_name.write_text(text)

        file_name = self._cfg.get_daily_data_path() / self._cfg.get_sources_file_name()
        file_name.write_text(text)

    def clear_daily_data(self, day_iso):
        import shutil
        daily_path = self._cfg.get_daily_data_path(day_iso)
        shutil.rmtree(daily_path)

