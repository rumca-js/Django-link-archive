import traceback
from django.db import models
from datetime import time, datetime, date, timedelta

from utils.dateutils import DateUtils

from .system import AppLogging


class DataExport(models.Model):
    EXPORT_TYPE_GIT = "export-type-git"
    EXPORT_TYPE_LOC = "export-type-loc"

    # fmt: off
    EXPORT_TYPE_CHOICES = (
        (EXPORT_TYPE_LOC, EXPORT_TYPE_LOC,),
        (EXPORT_TYPE_GIT, EXPORT_TYPE_GIT,),
    )
    # fmt: on

    EXPORT_DAILY_DATA = "export-dtype-daily-data"  # for each day a file is expected
    EXPORT_YEAR_DATA = "export-dtype-year-data"  # for each year a file is expected
    EXPORT_NOTIME_DATA = "export-dtype-notime-data"  # not a time related export. Will use other means for file, directory names

    # fmt: off
    EXPORT_DATA_CHOICES = (
        (EXPORT_DAILY_DATA, EXPORT_DAILY_DATA,),
        (EXPORT_YEAR_DATA, EXPORT_YEAR_DATA,),
        (EXPORT_NOTIME_DATA, EXPORT_NOTIME_DATA,),
    )
    # fmt: on

    enabled = models.BooleanField(default=True)
    export_type = models.CharField(max_length=1000, choices=EXPORT_TYPE_CHOICES)
    export_data = models.CharField(max_length=1000, choices=EXPORT_DATA_CHOICES)
    local_path = models.CharField(
        max_length=1000,
        default="./data",
        help_text="Local path is relative to main configuration export path. This path will be appended with app name and type of export",
    )
    remote_path = models.CharField(
        max_length=1000,
        blank=True,
        help_text="Example: https://github.com/rumca-js/Django-link-archive.git. Can be empty",
    )
    user = models.CharField(
        default="",
        max_length=2000,
        blank=True,
        help_text="Repo user name. Can be empty",
    )
    password = models.CharField(
        default="",
        max_length=2000,
        blank=True,
        help_text="Repo password, or token. Can be empty",
    )

    db_user = models.CharField(
        default="",
        max_length=2000,
        blank=True,
        help_text="This instance user for which data will be exporter. Example: bookmarks might be for each user separately. Can be empty",
    )

    # maybe we should make another table, for each EXPORT
    export_entries = models.BooleanField(default=True)
    export_entries_bookmarks = models.BooleanField(
        default=False, help_text="Export entries has to be checked for this to work"
    )
    export_entries_permanents = models.BooleanField(
        default=False, help_text="Export entries has to be checked for this to work"
    )

    export_sources = models.BooleanField(default=False)
    export_keywords = models.BooleanField(default=False)

    export_time = models.TimeField(
        default=time(0, 0), help_text="Time at which export is performed"
    )

    format_json = models.BooleanField(
        default=True, help_text="If set JSON files will be created"
    )
    format_md = models.BooleanField(default=True)
    format_rss = models.BooleanField(default=False)
    format_html = models.BooleanField(default=False)

    format_sources_opml = models.BooleanField(
        default=False,
        help_text="If enabled sources will be written in OPML format also",
    )

    output_zip = models.BooleanField(
        default=False, help_text="If enabled, output will be zipped"
    )
    output_sqlite = models.BooleanField(
        default=False, help_text="If enabled, output will be inserted into SQLite"
    )

    class Meta:
        ordering = ["-enabled", "export_type", "export_data"]

    def is_daily_data(self):
        return self.export_data == DataExport.EXPORT_DAILY_DATA

    def is_year_data(self):
        return self.export_data == DataExport.EXPORT_YEAR_DATA

    def is_notime_data(self):
        return self.export_data == DataExport.EXPORT_NOTIME_DATA

    def is_daily_data_set():
        exps = DataExport.objects.filter(
            export_data=DataExport.EXPORT_DAILY_DATA, enabled=True
        )

        if exps.count() > 0:
            return True
        else:
            return False

    def is_year_data_set():
        exps = DataExport.objects.filter(
            export_data=DataExport.EXPORT_YEAR_DATA, enabled=True
        )

        if exps.count() > 0:
            return True
        else:
            return False

    def is_notime_data_set():
        exps = DataExport.objects.filter(
            export_data=DataExport.EXPORT_NOTIME_DATA, enabled=True
        )

        if exps.count() > 0:
            return True
        else:
            return False

    def get_public_export_names():
        names = []

        exps = DataExport.objects.filter(
            export_type=DataExport.EXPORT_TYPE_GIT, enabled=True
        )

        for exp in exps:
            names.append(exp.remote_path)

        return names


class SourceExportHistory(models.Model):
    date = models.DateField(null=False)
    export = models.ForeignKey(
        DataExport,
        related_name="export_history",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-date"]

    def is_update_required(export):
        from ..configuration import Configuration

        yesterday = DateUtils.get_date_yesterday()

        history = SourceExportHistory.objects.filter(date=yesterday, export=export)

        if history.count() != 0:
            return False

        c = Configuration.get_object()

        now = DateUtils.get_datetime_now_utc()
        local = c.get_local_time_object(now)

        if local.time() < export.export_time:
            return False

        return True

    def get_safe():
        return SourceExportHistory.objects.all()[:7]

    def confirm(export, input_date=None):
        process_date = DateUtils.get_date_yesterday()
        if input_date is not None:
            process_date = input_date

        if (
            SourceExportHistory.objects.filter(date=process_date, export=export).count()
            == 0
        ):
            SourceExportHistory.objects.create(date=process_date, export=export)

    def cleanup(cfg=None):
        remove_threshold = datetime.today() - timedelta(days=30)
        histories = SourceExportHistory.objects.filter(date__lt=remove_threshold)
        histories.delete()
