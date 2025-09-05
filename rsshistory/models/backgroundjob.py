from django.conf import settings
from django.db import models

from ..apps import LinkDatabase
from .system import AppLogging


class BackgroundJob(models.Model):
    JOB_PROCESS_SOURCE = "process-source"
    JOB_LINK_ADD = "link-add"
    JOB_LINK_SAVE = "link-save"
    JOB_LINK_UPDATE_DATA = "link-update-data"
    JOB_LINK_RESET_DATA = "link-reset-data"
    JOB_LINK_RESET_LOCAL_DATA = "link-reset-local-data"
    JOB_LINK_DOWNLOAD_SOCIAL = "link-social-data"
    JOB_LINK_DOWNLOAD = "link-download"
    JOB_LINK_DOWNLOAD_MUSIC = "download-music"
    JOB_LINK_DOWNLOAD_VIDEO = "download-video"
    JOB_DOWNLOAD_FILE = "download-file"  # TODO stor file, should mention DB
    JOB_LINK_SCAN = "link-scan"
    JOB_SOURCE_ADD = "source-add"
    JOB_MOVE_TO_ARCHIVE = "move-to-archive"
    JOB_WRITE_DAILY_DATA = "write-daily-data"
    JOB_WRITE_YEAR_DATA = "write-year-data"
    JOB_WRITE_NOTIME_DATA = "write-notime-data"
    JOB_WRITE_TOPIC_DATA = "write-topic-data"
    JOB_IMPORT_DAILY_DATA = "import-daily-data"
    JOB_IMPORT_BOOKMARKS = "import-bookmarks"
    JOB_IMPORT_SOURCES = "import-sources"
    JOB_IMPORT_INSTANCE = "import-instance"
    JOB_IMPORT_FROM_FILES = "import-from-files"
    JOB_EXPORT_DATA = "export-data"
    JOB_CLEANUP = "cleanup"
    JOB_TRUNCATE_TABLE = "truncate-table"
    JOB_REMOVE = "remove"
    JOB_CHECK_DOMAINS = "check-domains"
    JOB_RUN_RULE = "run-rule"
    JOB_INITIALIZE = "initialize"
    JOB_INITIALIZE_BLOCK_LIST = (
        "initialize-block-list"  # initializes one specific block list
    )
    JOB_REFRESH = "refresh"

    # fmt: off
    JOB_CHOICES = (
        (JOB_PROCESS_SOURCE, JOB_PROCESS_SOURCE,),              # for RSS sources it checks if there are new data
        (JOB_LINK_ADD, JOB_LINK_ADD,),                          # adds link using default properties, may contain link map properties in the map
        (JOB_LINK_SAVE, JOB_LINK_SAVE,),                        # link is saved using thirdparty pages (archive.org)
        (JOB_LINK_UPDATE_DATA, JOB_LINK_UPDATE_DATA),           # fetches data from the internet, updates what is missing, updates page rating
        (JOB_LINK_RESET_DATA, JOB_LINK_RESET_DATA,),            # fetches data from the internet, replaces data, updates page rating
        (JOB_LINK_RESET_LOCAL_DATA, JOB_LINK_RESET_LOCAL_DATA,),# recalculates page rating
        (JOB_LINK_DOWNLOAD_SOCIAL, JOB_LINK_DOWNLOAD_SOCIAL,),  # downloads social data
        (JOB_LINK_DOWNLOAD, JOB_LINK_DOWNLOAD),                 # link is downloaded using wget
        (JOB_LINK_DOWNLOAD_MUSIC, JOB_LINK_DOWNLOAD_MUSIC),     #
        (JOB_LINK_DOWNLOAD_VIDEO, JOB_LINK_DOWNLOAD_VIDEO),     #
        (JOB_DOWNLOAD_FILE, JOB_DOWNLOAD_FILE),     #
        (JOB_LINK_SCAN, JOB_LINK_SCAN,),
        (JOB_SOURCE_ADD, JOB_SOURCE_ADD,),
        (JOB_MOVE_TO_ARCHIVE, JOB_MOVE_TO_ARCHIVE),
        (JOB_WRITE_DAILY_DATA, JOB_WRITE_DAILY_DATA),
        (JOB_WRITE_TOPIC_DATA, JOB_WRITE_TOPIC_DATA),
        (JOB_WRITE_YEAR_DATA, JOB_WRITE_YEAR_DATA),
        (JOB_WRITE_NOTIME_DATA, JOB_WRITE_NOTIME_DATA),
        (JOB_IMPORT_DAILY_DATA, JOB_IMPORT_DAILY_DATA),
        (JOB_IMPORT_BOOKMARKS, JOB_IMPORT_BOOKMARKS),
        (JOB_IMPORT_SOURCES, JOB_IMPORT_SOURCES),
        (JOB_IMPORT_INSTANCE, JOB_IMPORT_INSTANCE),
        (JOB_IMPORT_FROM_FILES, JOB_IMPORT_FROM_FILES),
        (JOB_EXPORT_DATA, JOB_EXPORT_DATA),
        (JOB_CLEANUP, JOB_CLEANUP),
        (JOB_TRUNCATE_TABLE, JOB_TRUNCATE_TABLE),
        (JOB_CHECK_DOMAINS, JOB_CHECK_DOMAINS),
        (JOB_INITIALIZE, JOB_INITIALIZE),
        (JOB_INITIALIZE_BLOCK_LIST, JOB_INITIALIZE_BLOCK_LIST),
        (JOB_RUN_RULE, JOB_RUN_RULE),
    )
    # fmt: on

    # job - add link, process source, download music, download video, wayback save
    job = models.CharField(max_length=1000, null=False)  # , choices=JOB_CHOICES)
    # task name
    task = models.CharField(max_length=1000, null=True)
    subject = models.CharField(max_length=1000, null=False)
    # task args "subject,arg1,arg2,..."
    # for add link, the first argument is the link URL
    # for download music, the first argument is the link URL
    args = models.CharField(max_length=1000, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    # smaller number = higher priority
    priority = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_jobs",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-enabled",
            "date_created",
            "job",
            "pk",
            "subject",
            "errors",
        ]

    def __str__(self):
        return "Job:{}\tSubject:{}\tArgs:{}\tDate Created:{}".format(
            self.job, self.subject, self.args, self.date_created
        )

    def save(self, *args, **kwargs):
        """
        We can fix some database errors here.
        We can trim title and description. No harm done.
        We cannot trim thumbnails, or link, it will not work after adding.
        """
        job_len = BackgroundJob._meta.get_field("job").max_length
        task_len = BackgroundJob._meta.get_field("task").max_length
        subject_len = BackgroundJob._meta.get_field("subject").max_length
        args_len = BackgroundJob._meta.get_field("args").max_length

        if self.job and len(self.job) >= job_len:
            AppLogging.error(
                "Job length is too long, cannot save",
                detail_text=str(self.job),
            )
            return

        if self.task and len(self.task) >= task_len:
            AppLogging.error(
                info_text="Job:{} Task length is too long, cannot save".format(
                    self.job
                ),
                detail_text=str(self.task),
            )
            return

        if self.subject and len(str(self.subject)) >= subject_len:
            AppLogging.error(
                "Job:{} Subject length is too long, cannot save".format(self.job),
                detail_text=str(self.subject),
            )
            return

        if self.args and len(self.args) >= args_len:
            AppLogging.error(
                "Job:{} Args length is too long, cannot save".format(self.job),
                detail_text=str(self.args),
            )
            return

        super().save(*args, **kwargs)


allowed_history_count = 500
class BackgroundJobHistory(models.Model):
    job = models.CharField(max_length=1000, null=False)
    task = models.CharField(max_length=1000, null=True)
    subject = models.CharField(max_length=1000, null=False)
    args = models.CharField(max_length=1000, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [
            "-date_created", # most recent up top
        ]

    def remove_old():
        history_count = BackgroundJobHistory.objects.all().count()
        if history_count > allowed_history_count:
            diff_history_count = history_count - allowed_history_count
            ids_to_delete = BackgroundJobHistory.objects.order_by("date_created").values_list('id', flat=True)[:diff_history_count]

            BackgroundJobHistory.objects.filter(id__in=ids_to_delete).delete()

    def mark_done(job_name, subject="", args="", task=None):
        BackgroundJobHistory.remove_old()

        jobs = BackgroundJobHistory.objects.filter(
            job=job_name, subject=subject, task=task, args=args
        )

        if jobs.exists():
            jobs.delete()

        return BackgroundJobHistory.objects.create(
            job=job_name, subject=subject, task=task, args=args
        )

    def mark_job_done(job, subject="", args="", task=None):
        BackgroundJobHistory.remove_old()

        if job is None:
            return

        jobs = BackgroundJobHistory.objects.filter(
            job=job.job, subject=job.subject, task=job.task, args=job.args
        )

        if jobs.exists():
            jobs.delete()

        return BackgroundJobHistory.objects.create(
            job=job.job, subject=job.subject, task=job.task, args=job.args
        )
