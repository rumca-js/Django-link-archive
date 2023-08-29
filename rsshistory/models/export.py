from django.db import models


class RssSourceExportHistory(models.Model):
    date = models.DateField(unique=True, null=False)

    class Meta:
        ordering = ["-date"]

    def is_update_required():
        from ..dateutils import DateUtils

        try:
            ob = ConfigurationEntry.get()
            if not ob.is_bookmark_repo_set() and not ob.is_daily_repo_set():
                return

            yesterday = DateUtils.get_date_yesterday()

            history = RssSourceExportHistory.objects.filter(date=yesterday)

            if len(history) != 0:
                return False
            return True

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception for update: {0} {1}".format(str(e), error_text)
            )

    def get_safe():
        return RssSourceExportHistory.objects.all()[:100]


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
