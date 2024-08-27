from utils.dateutils import DateUtils


class SourceEntriesDataWriter(object):
    def __init__(self, config, source_url):
        self._cfg = config
        self.source_url = source_url

    def write_for_day(self, input_path, day_iso):
        from ..controllers import LinkDataController
        from .entriesexporter import EntriesExporter

        date_range = DateUtils.get_range4day(day_iso)
        entries = LinkDataController.objects.filter(
            source=self.source_url, date_published__range=date_range
        )

        clean_url = self._cfg.get_url_clean_name(self.source_url)

        ex = EntriesExporter(self._cfg, entries)
        ex.export_entries(self.source_url, clean_url, input_path)


class SourcesEntriesDataWriter(object):
    def __init__(self, config):
        self._cfg = config

    def write_for_day(self, input_path, day_iso):
        """We do not want to provide for each day cumulative view. Users may want to select which 'streams' are selected individually '"""
        from ..controllers import SourceDataController, LinkDataController

        date_range = DateUtils.get_range4day(day_iso)

        # some entries might not have source in the database - added manually.
        # first capture entries, then check if has export to CMS.
        # if entry does not have source, it was added manually and is subject for export

        entries = LinkDataController.objects.filter(date_published__range=date_range)
        sources_urls = set(entries.values_list("source", flat=True).distinct())

        for source_url in sources_urls:
            source_objs = SourceDataController.objects.filter(url=source_url)
            if source_objs.exists() and not source_objs[0].export_to_cms:
                continue

            writer = SourceEntriesDataWriter(self._cfg, source_url)
            writer.write_for_day(input_path, day_iso)
