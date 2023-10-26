import logging
from pytz import timezone
from datetime import datetime, date

from django.db import models
from django.urls import reverse

from ..apps import LinkDatabase


class ConfigurationEntry(models.Model):
    ACCESS_TYPE_ALL = "access-type-all"
    ACCESS_TYPE_LOGGED = "access-type-logged"
    ACCESS_TYPE_OWNER = "access-type-owner"
    ACCESS_TYPE_STAFF = "access-type-staff"

    # fmt: off
    ACCESS_TYPES = (
        (ACCESS_TYPE_ALL, ACCESS_TYPE_ALL),                     #
        (ACCESS_TYPE_LOGGED, ACCESS_TYPE_LOGGED),               #
        (ACCESS_TYPE_OWNER, ACCESS_TYPE_OWNER),                 #
    )
    # fmt: on

    sources_refresh_period = models.IntegerField(default=3600)
    link_save = models.BooleanField(default=False)
    source_save = models.BooleanField(default=False)
    auto_store_entries = models.BooleanField(default=True)
    auto_store_sources = models.BooleanField(default=False)
    auto_store_sources_enabled = models.BooleanField(default=False)
    auto_store_domain_info = models.BooleanField(default=True)
    auto_store_keyword_info = models.BooleanField(default=True)
    track_user_actions = models.BooleanField(default=True)
    vote_min = models.IntegerField(default=-100)
    vote_max = models.IntegerField(default=100)
    number_of_comments_per_day = models.IntegerField(default=1)
    user_agent = models.CharField(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
        max_length=1000,
    )
    access_type = models.CharField(
        max_length=1000, null=False, choices=ACCESS_TYPES, default=ACCESS_TYPE_ALL
    )

    days_to_move_to_archive = models.IntegerField(default=100)
    days_to_remove_links = models.IntegerField(default=0)
    whats_new_days = models.IntegerField(default=7)

    data_import_path = models.CharField(
        default="../data/{}/imports".format(LinkDatabase.name),
        max_length=2000,
        null=True,
    )
    data_export_path = models.CharField(
        default="../data/{}/exports".format(LinkDatabase.name),
        max_length=2000,
        null=True,
    )
    # TODO selectable from combo?
    entries_order_by = models.CharField(
        default="-date_published",  # TODO support for multiple columns
        max_length=1000,
    )

    def get():
        confs = ConfigurationEntry.objects.all()
        if confs.count() == 0:
            return ConfigurationEntry.objects.create()
        else:
            return confs[0]

    def is_bookmark_repo_set(self):
        from .export import DataExport

        exps = DataExport.objects.filter(export_data=DataExport.EXPORT_BOOKMARKS)

        if exps.count() > 0:
            return True
        else:
            return False

    def is_daily_repo_set(self):
        from .export import DataExport

        exps = DataExport.objects.filter(export_data=DataExport.EXPORT_DAILY_DATA)

        if exps.count() > 0:
            return True
        else:
            return False

    def get_data_export_path(self):
        return self.data_export_path


class UserConfig(models.Model):
    DISPLAY_STYLE_LIGHT = "style-light"
    DISPLAY_STYLE_DARK = "style-dark"

    STYLE_TYPES = (
        (DISPLAY_STYLE_LIGHT, DISPLAY_STYLE_LIGHT),  #
        (DISPLAY_STYLE_DARK, DISPLAY_STYLE_DARK),  #
    )

    DISPLAY_TYPE_STANDARD = "standard"
    DISPLAY_TYPE_CLICKABLE_TAGS = "clickable-tags"
    DISPLAY_TYPE_LINE_AND_BUTTONS = "line-and-buttons"
    DISPLAY_TYPE_YOUTUBE_THUMBNAILS = "youtube-thumbnails"
    DISPLAY_TYPE_SEARCH_ENGINE = "search-engine"

    DISPLAY_TYPE_CHOICES = (
        (DISPLAY_TYPE_STANDARD, DISPLAY_TYPE_STANDARD),
        (DISPLAY_TYPE_CLICKABLE_TAGS, DISPLAY_TYPE_CLICKABLE_TAGS),
        (DISPLAY_TYPE_LINE_AND_BUTTONS, DISPLAY_TYPE_LINE_AND_BUTTONS),
        (DISPLAY_TYPE_YOUTUBE_THUMBNAILS, DISPLAY_TYPE_YOUTUBE_THUMBNAILS),
        (DISPLAY_TYPE_SEARCH_ENGINE, DISPLAY_TYPE_SEARCH_ENGINE),
    )

    user = models.CharField(max_length=500, unique=True)
    # theme: light, dark
    display_style = models.CharField(
        max_length=500, null=True, default="style-light", choices=STYLE_TYPES
    )
    # display type: standard, compact, preview
    display_type = models.CharField(
        max_length=500, null=True, default="standard", choices=DISPLAY_TYPE_CHOICES
    )
    show_icons = models.BooleanField(default=True)
    thumbnails_as_icons = models.BooleanField(default=True)
    small_icons = models.BooleanField(default=True)
    links_per_page = models.IntegerField(default=100)
    karma = models.IntegerField(default=0)

    def get(user_name=None):
        """
        This is used if no request is specified. Use configured by admin setup.
        """
        if user_name:
            confs = UserConfig.objects.filter(user=user_name)
            if confs.count() != 0:
                return confs[0]

        return UserConfig()

    def get_or_create(user_name):
        """
        This is used if no request is specified. Use configured by admin setup.
        """
        users = UserConfig.objects.filter(user=user_name)
        if not users.exists():
            user = UserConfig(user=user_name)
            user.save()
            return user
        return users[0]


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

        try:
            date_range = DateUtils.get_days_range(30)
            objs = PersistentInfo.objects.filter(date__lt=date_range[0])
            objs.delete()
        except Exception as e:
            pass


class BackgroundJob(models.Model):
    JOB_PROCESS_SOURCE = "process-source"
    JOB_LINK_ADD = "link-add"
    JOB_LINK_UPDATE_DATA = "link-update-data"
    JOB_LINK_SAVE = "link-save"
    JOB_LINK_DOWNLOAD = "link-download"
    JOB_LINK_DOWNLOAD_MUSIC = "download-music"
    JOB_LINK_DOWNLOAD_VIDEO = "download-video"
    JOB_WRITE_DAILY_DATA = "write-daily-data"
    JOB_WRITE_TOPIC_DATA = "write-topic-data"
    JOB_WRITE_BOOKMARKS = "write-bookmarks"
    JOB_IMPORT_DAILY_DATA = "import-daily-data"
    JOB_IMPORT_BOOKMARKS = "import-bookmarks"
    JOB_IMPORT_SOURCES = "import-sources"
    JOB_IMPORT_INSTANCE = "import-instance"
    JOB_PUSH_TO_REPO = "push-to-repo"
    JOB_PUSH_DAILY_DATA_TO_REPO = "push-daily-data-to-repo"
    JOB_CLEANUP = "cleanup"
    JOB_CHECK_DOMAINS = "check-domains"

    # fmt: off
    JOB_CHOICES = (
        (JOB_PROCESS_SOURCE, JOB_PROCESS_SOURCE,),              # for RSS sources it checks if there are new data
        (JOB_LINK_ADD, JOB_LINK_ADD,),                          # adds link using default properties, may contain link map properties in the map
        (JOB_LINK_UPDATE_DATA, JOB_LINK_UPDATE_DATA),           # update data, recalculate
        (JOB_LINK_SAVE, JOB_LINK_SAVE,),                        # link is saved using thirdparty pages (archive.org)
        (JOB_LINK_DOWNLOAD, JOB_LINK_DOWNLOAD),                 # link is downloaded using wget
        (JOB_LINK_DOWNLOAD_MUSIC, JOB_LINK_DOWNLOAD_MUSIC),     #
        (JOB_LINK_DOWNLOAD_VIDEO, JOB_LINK_DOWNLOAD_VIDEO),     #
        (JOB_WRITE_DAILY_DATA, JOB_WRITE_DAILY_DATA),
        (JOB_WRITE_TOPIC_DATA, JOB_WRITE_TOPIC_DATA),
        (JOB_WRITE_BOOKMARKS, JOB_WRITE_BOOKMARKS),
        (JOB_IMPORT_DAILY_DATA, JOB_IMPORT_DAILY_DATA),
        (JOB_IMPORT_BOOKMARKS, JOB_IMPORT_BOOKMARKS),
        (JOB_IMPORT_SOURCES, JOB_IMPORT_SOURCES),
        (JOB_IMPORT_INSTANCE, JOB_IMPORT_INSTANCE),
        (JOB_PUSH_TO_REPO, JOB_PUSH_TO_REPO),
        (JOB_PUSH_DAILY_DATA_TO_REPO, JOB_PUSH_DAILY_DATA_TO_REPO),
        (JOB_CLEANUP, JOB_CLEANUP),
        (JOB_CHECK_DOMAINS, JOB_CHECK_DOMAINS),
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
