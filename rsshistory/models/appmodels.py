import logging
from pytz import timezone
from datetime import datetime, date

from django.db import models
from django.urls import reverse

from ..apps import LinkDatabase


class ConfigurationEntry(models.Model):
    data_import_path = models.CharField(
        default="./data/imports", max_length=2000, null=True
    )
    data_export_path = models.CharField(
        default="./data/exports", max_length=2000, null=True
    )
    git_path = models.CharField(default="./data/git", max_length=2000, null=True)
    git_user = models.CharField(default="", max_length=2000, null=True)
    git_token = models.CharField(default="", max_length=2000, null=True)
    git_repo = models.CharField(default="", max_length=2000, null=True)
    git_daily_repo = models.CharField(default="", max_length=2000, null=True)
    sources_refresh_period = models.IntegerField(default=3600)
    link_archive = models.BooleanField(default=True)
    source_archive = models.BooleanField(default=True)

    def get():
        confs = ConfigurationEntry.objects.all()
        if len(confs) == 0:
            return ConfigurationEntry.objects.create()
        else:
            return confs[0]

    def is_bookmark_repo_set(self):
        if (
            self.git_repo == ""
            or self.git_user == ""
            and self.git_token == ""
            or self.git_repo == None
            or self.git_user == None
            or self.git_token == None
        ):
            return False
        else:
            return True

    def is_daily_repo_set(self):
        if (
            self.git_daily_repo == ""
            or self.git_user == ""
            or self.git_token == ""
            or self.git_daily_repo == None
            or self.git_user == None
            or self.git_token == None
        ):
            return False
        else:
            return True

    def get_data_export_path(self):
        return self.data_export_path


class UserConfig(models.Model):
    THEME_TYPE_CHOICES = (
        ("light", "light"),
        ("dark", "dark"),
    )

    DISPLAY_TYPE_CHOICES = (
        ("standard", "standard"),
        ("clickable-tags", "clickable-tags"),
        ("line-and-buttons", "line-and-buttons"),
        ("youtube-thumbnails", "youtube-thumbnails"),
    )

    user = models.CharField(max_length=500, unique=True)
    # theme: light, dark
    theme = models.CharField(
        max_length=500, null=True, default="light", choices=THEME_TYPE_CHOICES
    )
    # display type: standard, compact, preview
    display_type = models.CharField(
        max_length=500, null=True, default="standard", choices=DISPLAY_TYPE_CHOICES
    )
    show_icons = models.BooleanField(default=True)
    thumbnails_as_icons = models.BooleanField(default=True)
    small_icons = models.BooleanField(default=True)
    links_per_page = models.IntegerField(default=100)

    def get(user_name=None):
        """
        This is used if no request is specified. Use configured by admin setup.
        """
        if user_name:
            confs = UserConfig.objects.filter(user=user_name)
            if len(confs) != 0:
                return confs[0]

        confs = UserConfig.objects.all()
        if len(confs) != 0:
            return confs[0]

        return UserConfig()


class PersistentInfo(models.Model):
    info = models.CharField(default="", max_length=2000)
    level = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.now)
    user = models.CharField(max_length=1000, null=True)

    class Meta:
        ordering = ["-date", "level"]

    def create(info, level=int(logging.INFO), user=None):
        PersistentInfo.remove_old_ones()

        ob = PersistentInfo(
            info=info, level=level, date=datetime.now(timezone("UTC")), user=user
        )

        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def text(info, level=int(logging.INFO), user=None):
        PersistentInfo.remove_old_ones()

        ob = PersistentInfo(
            info=info, level=level, date=datetime.now(timezone("UTC")), user=user
        )
        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def error(info, level=int(logging.ERROR), user=None):
        PersistentInfo.remove_old_ones()

        ob = PersistentInfo(
            info=info, level=level, date=datetime.now(timezone("UTC")), user=user
        )
        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def exc(info, level=int(logging.ERROR), exc_data=None, user=None):
        PersistentInfo.remove_old_ones()

        text = "{}. Exception data:\n{}".format(info, str(exc_data))
        ob = PersistentInfo(
            info=text, level=level, date=datetime.now(timezone("UTC")), user=user
        )

        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def cleanup():
        PersistentInfo.remove_old_ones()

        obs = PersistentInfo.objects.filter(level=int(logging.INFO))
        if obs.exists():
            obs.delete()

    def truncate():
        PersistentInfo.objects.all().delete()

    def get_safe():
        return PersistentInfo.objects.all()[0:100]

    def remove_old_ones():
        from ..dateutils import DateUtils

        date_range = DateUtils.get_days_range(30)
        objs = PersistentInfo.objects.filter(date__lt=date_range[0])
        objs.delete()


class BackgroundJob(models.Model):
    JOB_PROCESS_SOURCE = "process-source"
    JOB_LINK_ADD = "link-add"
    JOB_LINK_DETAILS = "link-details"
    JOB_LINK_REFRESH = "link-refresh"
    JOB_LINK_ARCHIVE = "link-archive"
    JOB_LINK_DOWNLOAD = "link-download"
    JOB_LINK_DOWNLOAD_MUSIC = "download-music"
    JOB_LINK_DOWNLOAD_VIDEO = "download-video"
    JOB_WRITE_DAILY_DATA = "write-daily-data"
    JOB_WRITE_TOPIC_DATA = "write-topic-data"
    JOB_WRITE_BOOKMARKS = "write-bookmarks"
    JOB_IMPORT_DAILY_DATA = "import-daily-data"
    JOB_IMPORT_BOOKMARKS = "import-bookmarks"
    JOB_IMPORT_SOURCES = "import-sources"
    JOB_PUSH_TO_REPO = "push-to-repo"
    JOB_PUSH_DAILY_DATA_TO_REPO = "push-daily-data-to-repo"

    # fmt: off
    JOB_CHOICES = (
        (JOB_PROCESS_SOURCE, JOB_PROCESS_SOURCE,),              # for RSS sources it checks if there are new data
        (JOB_LINK_ADD, JOB_LINK_ADD,),                          # adds link using default properties, may contain link map properties in the map
        (JOB_LINK_DETAILS, JOB_LINK_DETAILS),                   # fetches link additional information
        (JOB_LINK_REFRESH, JOB_LINK_REFRESH),                   # refreshes link, refetches its data
        (JOB_LINK_ARCHIVE, JOB_LINK_ARCHIVE,),                  # link is archived using thirdparty pages (archive.org)
        (JOB_LINK_DOWNLOAD, JOB_LINK_DOWNLOAD),                 # link is downloaded using wget
        (JOB_LINK_DOWNLOAD_MUSIC, JOB_LINK_DOWNLOAD_MUSIC),     #
        (JOB_LINK_DOWNLOAD_VIDEO, JOB_LINK_DOWNLOAD_VIDEO),     #
        (JOB_WRITE_DAILY_DATA, JOB_WRITE_DAILY_DATA),
        (JOB_WRITE_TOPIC_DATA, JOB_WRITE_TOPIC_DATA),
        (JOB_WRITE_BOOKMARKS, JOB_WRITE_BOOKMARKS),
        (JOB_IMPORT_DAILY_DATA, JOB_IMPORT_DAILY_DATA),
        (JOB_IMPORT_BOOKMARKS, JOB_IMPORT_BOOKMARKS),
        (JOB_IMPORT_SOURCES, JOB_IMPORT_SOURCES),
        (JOB_PUSH_TO_REPO, JOB_PUSH_TO_REPO),
        (JOB_PUSH_DAILY_DATA_TO_REPO, JOB_PUSH_DAILY_DATA_TO_REPO),
    )
    # fmt: on

    # job - add link, process source, download music, download video, wayback save
    job = models.CharField(max_length=1000, null=False, choices=JOB_CHOICES)
    # task name
    task = models.CharField(max_length=1000, null=True)
    subject = models.CharField(max_length=1000, null=False)
    # task args "subject,arg1,arg2,..."
    # for add link, the first argument is the link URL
    # for download music, the first argument is the link URL
    args = models.CharField(max_length=1000, null=True)

    class Meta:
        ordering = ["job", "pk", "subject"]
