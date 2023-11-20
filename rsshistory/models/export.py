import traceback
from django.db import models

from .admin import PersistentInfo


class SourceExportHistory(models.Model):
    date = models.DateField(unique=True, null=False)

    class Meta:
        ordering = ["-date"]

    def is_update_required():
        from ..dateutils import DateUtils

        try:
            yesterday = DateUtils.get_date_yesterday()

            history = SourceExportHistory.objects.filter(date=yesterday)

            if history.count() != 0:
                return False
            return True

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception for update: {0} {1}".format(str(e), error_text)
            )

    def get_safe():
        return SourceExportHistory.objects.all()[:7]

    def confirm(input_date=None):
        from ..dateutils import DateUtils

        process_date = DateUtils.get_date_yesterday()
        if input_date is not None:
            process_date = input_date

        if SourceExportHistory.objects.filter(date=process_date).count() == 0:
            SourceExportHistory.objects.create(date=process_date)


class DataExport(models.Model):
    EXPORT_TYPE_GIT = "export-type-git"
    EXPORT_TYPE_LOC = "export-type-loc"

    # fmt: off
    EXPORT_TYPE_CHOICES = (
        (EXPORT_TYPE_LOC, EXPORT_TYPE_LOC,),
        (EXPORT_TYPE_GIT, EXPORT_TYPE_GIT,),
    )
    # fmt: on

    EXPORT_DAILY_DATA = "export-dtype-daily-data"       # for each day a file is expected
    EXPORT_YEAR_DATA = "export-dtype-year-data"         # for each year a file is expected
    EXPORT_NOTIME_DATA = "export-dtype-notime-data"     # not a time related export. Will use other means for file, directory names

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
    local_path = models.CharField(max_length=1000)  # relative?
    remote_path = models.CharField(max_length=1000)
    user = models.CharField(default="", max_length=2000, null=True)
    password = models.CharField(default="", max_length=2000, null=True)

    # maybe we should make another table, for each EXPORT
    export_entries = models.BooleanField(default=True)
    export_entries_bookmarks = models.BooleanField(default=False)
    export_entries_permanents = models.BooleanField(default=False)
    export_sources = models.BooleanField(default=False)

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
