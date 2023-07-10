"""
"""

import traceback
import logging
from datetime import datetime, date

from django.db import models
from django.urls import reverse

from pytz import timezone

from .apps import LinkDatabase


class SourceDataModel(models.Model):
    SOURCE_TYPE_RSS = "BaseRssPlugin"
    SOURCE_TYPE_PARSE = "BaseParsePlugin"
    SOURCE_TYPE_GENEROUS_PARSE = "SourceGenerousParserPlugin"
    SOURCE_TYPE_CODEPROJECT = "CodeProjectPlugin"
    SOURCE_TYPE_INSTALKI = "InstalkiPlugin"
    SOURCE_TYPE_DIGITS_START = "SourceParseDigitsPlugin"
    SOURCE_TYPE_TVN24 = "TVN24Plugin"
    SOURCE_TYPE_SPOTIFY = "SpotifyPlugin"

    # fmt: off
    SOURCE_TYPES = (
        (SOURCE_TYPE_RSS, SOURCE_TYPE_RSS),                     #
        (SOURCE_TYPE_PARSE, SOURCE_TYPE_PARSE),                 #
        (SOURCE_TYPE_GENEROUS_PARSE, SOURCE_TYPE_GENEROUS_PARSE),                 #
        (SOURCE_TYPE_CODEPROJECT, SOURCE_TYPE_CODEPROJECT),     #
        (SOURCE_TYPE_INSTALKI, SOURCE_TYPE_INSTALKI),           #
        (SOURCE_TYPE_DIGITS_START, SOURCE_TYPE_DIGITS_START),       #
        (SOURCE_TYPE_TVN24, SOURCE_TYPE_TVN24),                 #
        (SOURCE_TYPE_SPOTIFY, SOURCE_TYPE_SPOTIFY),             #
    )
    # fmt: on

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    category = models.CharField(max_length=1000)
    subcategory = models.CharField(max_length=1000)
    dead = models.BooleanField(default=False)
    export_to_cms = models.BooleanField(default=False)
    remove_after_days = models.CharField(max_length=10, default="0")
    language = models.CharField(max_length=1000, default="en-US")
    favicon = models.CharField(max_length=1000, null=True)
    on_hold = models.BooleanField(default=False)
    fetch_period = models.IntegerField(default=3600)
    source_type = models.CharField(
        max_length=1000, null=False, choices=SOURCE_TYPES, default=SOURCE_TYPE_RSS
    )

    class Meta:
        ordering = ["title"]


class SourceOperationalData(models.Model):
    url = models.CharField(max_length=2000, unique=True)
    date_fetched = models.DateTimeField(null=True)
    import_seconds = models.IntegerField(null=True)
    number_of_entries = models.IntegerField(null=True)
    source_obj = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="dynamic_data",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["date_fetched"]


class RssSourceExportHistory(models.Model):
    date = models.DateField(unique=True, null=False)

    class Meta:
        ordering = ["-date"]

    def is_update_required():
        from .dateutils import DateUtils

        try:
            ob = ConfigurationEntry.get()
            if not ob.is_git_set():
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


class LinkDataModel(models.Model):
    source = models.CharField(max_length=2000)
    title = models.CharField(max_length=1000, null=True)
    description = models.TextField(max_length=1000, null=True)
    link = models.CharField(max_length=1000, unique=True)
    date_published = models.DateTimeField(default=datetime.now)
    # this entry cannot be removed
    persistent = models.BooleanField(default=False)
    # this entry is dead indication
    dead = models.BooleanField(default=False)
    artist = models.CharField(max_length=1000, null=True, default=None)
    album = models.CharField(max_length=1000, null=True, default=None)
    # user who added entry
    user = models.CharField(max_length=1000, null=True, default=None)

    # possible values en-US, or pl_PL
    language = models.CharField(max_length=10, null=True, default=None)
    thumbnail = models.CharField(max_length=1000, null=True, default=None)

    source_obj = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="link_source",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-date_published", "source", "title"]


class ArchiveLinkDataModel(models.Model):
    source = models.CharField(max_length=2000)
    title = models.CharField(max_length=1000, null=True)
    description = models.TextField(max_length=1000, null=True)
    link = models.CharField(max_length=1000, unique=True)
    date_published = models.DateTimeField(default=datetime.now)
    # this entry cannot be removed
    persistent = models.BooleanField(default=False)
    # this entry is dead indication
    dead = models.BooleanField(default=False)
    artist = models.CharField(max_length=1000, null=True, default=None)
    album = models.CharField(max_length=1000, null=True, default=None)
    # user who added entry
    user = models.CharField(max_length=1000, null=True, default=None)

    # possible values en-US, or pl_PL
    language = models.CharField(max_length=10, null=True, default=None)
    thumbnail = models.CharField(max_length=1000, null=True, default=None)

    source_obj = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="archive_source",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-date_published", "source", "title"]


class LinkTagsDataModel(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields

    link = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    date = models.DateTimeField(default=datetime.now)
    tag = models.CharField(max_length=1000)

    link_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="tags",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-date"]

    def get_delim():
        return ","

    def join_elements(elements):
        tag_string = ""
        for element in elements:
            if tag_string == "":
                tag_string = element.tag
            else:
                tag_string += LinkTagsDataModel.get_delim() + element.tag

        return tag_string

    def get_author_tag_string(author, link):
        current_tags_objs = LinkTagsDataModel.objects.filter(link=link, author=author)

        if current_tags_objs.exists():
            return LinkTagsDataModel.join_elements(current_tags_objs)


class LinkVoteDataModel(models.Model):
    author = models.CharField(max_length=1000)
    vote = models.IntegerField(default=0)

    link_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="votes",
        null=True,
        blank=True,
    )


class LinkCommentDataModel(models.Model):
    author = models.CharField(max_length=1000)
    comment = models.TextField(max_length=3000)
    date_published = models.DateTimeField(default=datetime.now)
    date_edited = models.DateTimeField(null=True)
    reply_id = models.IntegerField(null=True)

    link_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )


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

    # TODO remove this function. refactor to two functions
    def is_git_set(self):
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

    def is_git_daily_set(self):
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
        from .dateutils import DateUtils

        date_range = DateUtils.get_days_range(30)
        objs = PersistentInfo.objects.filter(date__lt=date_range[0])
        objs.delete()


""" YouTube meta cache """


class YouTubeMetaCache(models.Model):
    url = models.CharField(max_length=1000, help_text="url", unique=False)
    details_json = models.CharField(max_length=1000, help_text="details_json")
    dead = models.BooleanField(default=False, help_text="dead")

    link_yt_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.SET_NULL,
        related_name="link_yt",
        null=True,
        blank=True,
    )


class YouTubeReturnDislikeMetaCache(models.Model):
    url = models.CharField(max_length=1000, help_text="url", unique=False)
    return_dislike_json = models.CharField(
        max_length=1000, help_text="return_dislike_json"
    )
    dead = models.BooleanField(default=False, help_text="dead")

    link_rd_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.SET_NULL,
        related_name="link_rd",
        null=True,
        blank=True,
    )


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
