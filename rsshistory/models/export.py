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

    EXPORT_DAILY_DATA = "export-dtype-daily-data"
    EXPORT_BOOKMARKS = "export-dtype-bookmarks"

    # fmt: off
    EXPORT_DATA_CHOICES = (
        (EXPORT_DAILY_DATA, EXPORT_DAILY_DATA,),
        (EXPORT_BOOKMARKS, EXPORT_BOOKMARKS,),
    )
    # fmt: on

    enabled = models.BooleanField(default=True)
    export_type = models.CharField(max_length=1000, choices=EXPORT_TYPE_CHOICES)
    export_data = models.CharField(max_length=1000, choices=EXPORT_DATA_CHOICES)
    local_path = models.CharField(max_length=1000)
    remote_path = models.CharField(max_length=1000)
    user = models.CharField(default="", max_length=2000, null=True)
    password = models.CharField(default="", max_length=2000, null=True)

    # maybe we should make another table, for each EXPORT
    export_entries = models.BooleanField(default=True)
    export_entries_bookmarks = models.BooleanField(default=False)
    export_entries_permanents = models.BooleanField(default=False)
    export_sources = models.BooleanField(default=False)
