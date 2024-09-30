import logging
import traceback
from pathlib import Path

from pytz import timezone
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.templatetags.static import static

from ..webtools.ipc import DEFAULT_PORT
from utils.dateutils import DateUtils

from ..apps import LinkDatabase


DISPLAY_STYLE_LIGHT = "style-light"
DISPLAY_STYLE_DARK = "style-dark"

STYLE_TYPES = (
    (DISPLAY_STYLE_LIGHT, DISPLAY_STYLE_LIGHT),  #
    (DISPLAY_STYLE_DARK, DISPLAY_STYLE_DARK),  #
)


class ConfigurationEntry(models.Model):
    # fmt: off
    ACCESS_TYPE_ALL = "access-type-all"
    ACCESS_TYPE_LOGGED = "access-type-logged"
    ACCESS_TYPE_OWNER = "access-type-owner"
    ACCESS_TYPE_STAFF = "access-type-staff"

    ACCESS_TYPES = (
        (ACCESS_TYPE_ALL, ACCESS_TYPE_ALL),                     #
        (ACCESS_TYPE_LOGGED, ACCESS_TYPE_LOGGED),               #
        (ACCESS_TYPE_OWNER, ACCESS_TYPE_OWNER),                 #
    )

    DISPLAY_TYPE_STANDARD = "standard"
    DISPLAY_TYPE_CLICKABLE_TAGS = "clickable-tags"
    DISPLAY_TYPE_LINE_AND_BUTTONS = "line-and-buttons"
    DISPLAY_TYPE_GALLERY = "gallery"
    DISPLAY_TYPE_SEARCH_ENGINE = "search-engine"

    DISPLAY_TYPE_CHOICES = (
        (DISPLAY_TYPE_STANDARD, DISPLAY_TYPE_STANDARD),
        (DISPLAY_TYPE_CLICKABLE_TAGS, DISPLAY_TYPE_CLICKABLE_TAGS),
        (DISPLAY_TYPE_LINE_AND_BUTTONS, DISPLAY_TYPE_LINE_AND_BUTTONS),
        (DISPLAY_TYPE_GALLERY, DISPLAY_TYPE_GALLERY),
        (DISPLAY_TYPE_SEARCH_ENGINE, DISPLAY_TYPE_SEARCH_ENGINE),
    )

    # fmt: on
    instance_title = models.CharField(
        default="Personal Link Database",
        max_length=500,
        help_text="Instance title",
    )

    instance_description = models.CharField(
        default="Personal Link Database. May work as link aggregator, may link as YouTube subscription filter.",
        max_length=500,
        help_text="Instance description",
    )

    instance_internet_location = models.CharField(
        blank=True,
        max_length=200,
        help_text="Instance location. For example https://my-domain.com/apps/rsshistory/",
    )

    favicon_internet_location = models.CharField(
        default="",
        max_length=200,
        help_text="Instance location. For example https://my-domain.com/apps/rsshistory/static/rsshistory/icons/favicon.ico",
    )

    admin_user = models.CharField(
        max_length=500, default="admin", blank=True, help_text="Admin user name"
    )

    access_type = models.CharField(
        max_length=100,
        null=False,
        choices=ACCESS_TYPES,
        default=ACCESS_TYPE_ALL,
        help_text='There are three access types available. "All" allows anybody view contents. "Logged" allows only logged users to view contents. "Owner" means application is private, and only owner can view it\'s contents.',
    )

    logging_level = models.IntegerField(default=int(logging.WARNING))

    initialized = models.BooleanField(
        default=False,
    )

    background_tasks = models.BooleanField(
        default=True,
        help_text="If disabled, background tasks, and jobs are disabled.",
    )

    data_import_path = models.CharField(
        default="../data/imports",
        max_length=2000,
        null=True,
    )
    data_export_path = models.CharField(
        default="../data/exports",
        max_length=2000,
        null=True,
    )

    auto_store_thumbnails = models.BooleanField(
        default=False,
        help_text="Automatically stores thumbnail. Available when file support is enabled",
    )

    # features

    enable_keyword_support = models.BooleanField(
        default=True, help_text="Enable keyword feature support"
    )

    enable_domain_support = models.BooleanField(
        default=True, help_text="Enable domain feature support"
    )

    enable_file_support = models.BooleanField(
        default=False, help_text="Enable file feature support"
    )

    link_save = models.BooleanField(
        default=False, help_text="Links are saved using archive.org."
    )

    source_save = models.BooleanField(
        default=False, help_text="Links are saved using archive.org."
    )

    # database link contents

    accept_dead = models.BooleanField(
        default=False,
        help_text="Accept rotten links, no longer active, to be added to the database",
    )  # whether dead entries can be introduced into database

    accept_ip_addresses = models.BooleanField(
        default=False,
        help_text="Accept IP addressed links, like //127.0.0.1/my/directory",
    )

    accept_domains = models.BooleanField(
        default=True, help_text="Domain links can be added to system"
    )

    accept_not_domain_entries = models.BooleanField(
        default=True, help_text="Links that are not domains can be added to system"
    )

    keep_domains = models.BooleanField(
        default=False, help_text="If true domains will be made permanent"
    )

    keep_permanent_items = models.BooleanField(
        default=True, help_text="This affects permament and bookmarked status entries"
    )

    auto_scan_entries = models.BooleanField(
        default=False,
        help_text="Scans for new links, when link is added. From decription, from contents",
    )

    new_entries_merge_data = models.BooleanField(
        default=False,
        help_text="Tries to merge data for new entries - captures what is missing",
    )

    new_entries_use_clean_data = models.BooleanField(
        default=False,
        help_text="Fetches clean information from the Internet for new entries",
    )

    auto_create_sources = models.BooleanField(  # TODO rename to auto_create_sources?
        default=False,
        help_text="Adds any new found source",
    )

    new_source_enabled_state = models.BooleanField(
        default=False, help_text="Default state of a new source"
    )

    prefer_https = models.BooleanField(
        default=True,
        help_text="Https is preferred. If update takes place, and https is available, we upgrade link.",
    )

    prefer_non_www_sites = models.BooleanField(
        default=False,
        help_text="Non www sites are preferred. If update takes place www links could be replaced with clean links without it.",
    )

    block_keywords = models.CharField(
        max_length=1000,
        blank=True,
        default="mastubat, porn",
        help_text="Links with these keywords will be blocked",
    )

    # updates

    sources_refresh_period = models.IntegerField(
        default=3600,
        help_text="Unit [s]. Defines how often sources are checked for data.",
    )

    days_to_move_to_archive = models.IntegerField(
        default=50,
        help_text="Number of days, after which entries are moved to archive. Disabled if 0.",
    )

    days_to_remove_links = models.IntegerField(
        default=100,
        help_text="Number of days, after which links are removed. Disabled if 0.",
    )

    days_to_remove_stale_entries = models.IntegerField(
        default=35, help_text="Number of days after which dead entries are removed"
    )

    days_to_check_std_entries = models.IntegerField(
        default=35,
        help_text="Number of days after which normal entries are checked for status",
    )

    days_to_check_stale_entries = models.IntegerField(
        default=35,
        help_text="Number of days after which dead entries are checked for status",
    )

    number_of_update_entries = models.IntegerField(
        default=1,
        help_text="The amount of entries that will be updated at each refresh",
    )

    # Networking

    ssl_verification = models.BooleanField(
        default=True
    )  # Might work faster if disabled, but might capture invalid pages

    user_agent = models.CharField(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
        max_length=500,
        help_text='You can check your user agent in <a href="https://www.supermonitoring.com/blog/check-browser-http-headers/">https://www.supermonitoring.com/blog/check-browser-http-headers/</a>.',
    )

    user_headers = models.CharField(
        max_length=1000,
        blank=True,
        help_text='Provide JSON configuration of headers. You can check your user agent in <a href="https://www.supermonitoring.com/blog/check-browser-http-headers/">https://www.supermonitoring.com/blog/check-browser-http-headers/</a>.',
    )

    internet_test_page = models.CharField(
        default="https://google.com",
        max_length=2000,
        null=True,
        help_text="Page that is pinged to check if Internet is OK",
    )

    respect_robots_txt = models.BooleanField(
        default=False,
        help_text="Use robots.txt information. Some functionality can not work: for example YouTube channels",
    )

    # User settings

    track_user_actions = models.BooleanField(
        default=True, help_text="Among tracked elements: what is searched."
    )

    track_user_searches = models.BooleanField(default=True)

    track_user_navigation = models.BooleanField(default=False)

    max_number_of_searches = models.IntegerField(default=300)

    vote_min = models.IntegerField(default=-100)

    vote_max = models.IntegerField(default=100)

    number_of_comments_per_day = models.IntegerField(
        default=1,
        help_text="The limit is for each user. Helps in maintaining proper culture",
    )

    # display

    time_zone = models.CharField(
        max_length=50,
        default="UTC",
        help_text="List of available timezones can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones. For example Europe/Warsaw",
    )

    whats_new_days = models.IntegerField(
        default=7, help_text="What's new page time range in days"
    )

    # TODO selectable from combo?
    entries_order_by = models.CharField(
        default="-date_published",  # TODO support for multiple columns
        max_length=1000,
        help_text="For Google-like experience set -page_rating. By default it is set to order of publication, -date_published.",
    )

    display_style = models.CharField(
        max_length=500, null=True, 
        default="style-light",
        choices=STYLE_TYPES,
        help_text="Applies to not logged users",
    )
    display_type = models.CharField(
        max_length=500,
        null=True,
        default="standard",
        choices=DISPLAY_TYPE_CHOICES,
        help_text="Applies to not logged users",
    )
    show_icons = models.BooleanField(default=True,
        help_text="Applies to not logged users",
        )
    thumbnails_as_icons = models.BooleanField(
        default=True, help_text="If false, source favicons are used as thumbnails. Applies to not logged users",
    )
    small_icons = models.BooleanField(default=True,
        help_text="Applies to not logged users",
    )
    local_icons = models.BooleanField(
        default=False, help_text="If true, only locally stored icons are displayed. Applies to not logged users",
    )

    links_per_page = models.IntegerField(
        default=100, help_text="Number of links per page. Applies to not logged users",
    )
    sources_per_page = models.IntegerField(
        default=100, help_text="Number of sources per page. Applies to not logged users"
    )

    max_links_per_page = models.IntegerField(default=100, help_text="Maximum number of links per page")
    max_sources_per_page = models.IntegerField(default=100, help_text="Maximum number of sources per page")
    max_number_of_related_links = models.IntegerField(default=30, help_text="Maximum number of entries displayed in 'entry detail related' view")

    debug_mode = models.BooleanField(
        default=False,
        help_text="Debug mode allows to see errors more clearly",
    )

    def get():
        """
        Most probably should not be used directly. Should be cached in application
        """
        confs = ConfigurationEntry.objects.all()
        if confs.count() == 0:
            return ConfigurationEntry.objects.create()
        else:
            return confs[0]

    def get_data_export_path(self):
        return self.data_export_path

    def get_entries_order_by(self):
        """
        @note valid example "-date_published, -page_rating"
        @result tuple of order bies
        """
        input_string = self.entries_order_by
        delimiter = ","
        result_list = [item.strip() for item in input_string.split(delimiter)]
        return result_list

    def save(self, *args, **kwargs):
        """
        Fix errors here
        """

        users = User.objects.filter(username=self.admin_user)
        if users.count() == 0:
            self.admin_user = ""

        try:
            tzn = timezone(self.time_zone)
        except Exception as E:
            self.time_zone = "UTC"

        super().save(*args, **kwargs)


class SystemOperation(models.Model):
    thread_id = models.CharField(
        blank=True,
        help_text="Thread ID",
        max_length=100,
    )

    date_created = models.DateTimeField(auto_now_add=True, null=True)

    is_internet_connection_checked = models.BooleanField(
        default=False,
        help_text="Is connection OK",
    )

    is_internet_connection_ok = models.BooleanField(
        default=True,
        help_text="Is connection OK",
    )

    class Meta:
        ordering = ["-date_created"]

    def cleanup():
        all_entries = SystemOperation.objects.filter(date_created__isnull=True)
        all_entries.delete()

        thread_ids = SystemOperation.get_thread_ids()
        for thread_id in thread_ids:
            # leave one entry with time check
            all_entries = SystemOperation.objects.filter(
                thread_id=thread_id, is_internet_connection_checked=True
            )
            if all_entries.exists() and all_entries.count() > 1:
                entries = all_entries[1:]
                for entry in entries:
                    entry.delete()

            # leave one entry without time check
            all_entries = SystemOperation.objects.filter(
                thread_id=thread_id, is_internet_connection_checked=False
            )
            if all_entries.exists() and all_entries.count() > 1:
                entries = all_entries[1:]
                for entry in entries:
                    entry.delete()

    def is_internet_ok():
        entries = SystemOperation.objects.filter(is_internet_connection_checked=True)
        if entries.exists():
            return entries[0].is_internet_connection_ok
        else:
            return True

    def get_last_thread_signal(thread_id):
        entries = SystemOperation.objects.filter(thread_id=thread_id)

        if entries.exists():
            return entries[0].date_created

    def get_last_internet_check():
        entries = SystemOperation.objects.filter(is_internet_connection_checked=True)

        if entries.exists():
            return entries[0].date_created

    def get_last_internet_status():
        entries = SystemOperation.objects.filter(is_internet_connection_checked=True)

        if entries.exists():
            return entries[0].is_internet_connection_ok

    def add_by_thread(
        thread_id, internet_status_checked=False, internet_status_ok=True
    ):
        # delete all entries without internet check
        all_entries = SystemOperation.objects.filter(
            thread_id=thread_id, is_internet_connection_checked=False
        )
        all_entries.delete()

        # leave one entry with time check
        all_entries = SystemOperation.objects.filter(
            thread_id=thread_id, is_internet_connection_checked=True
        )
        if all_entries.exists() and all_entries.count() > 1:
            entries = all_entries[1:]
            for entry in entries:
                entry.delete()

        SystemOperation.objects.create(
            thread_id=thread_id,
            is_internet_connection_checked=internet_status_checked,
            is_internet_connection_ok=internet_status_ok,
        )

    def get_thread_ids():
        from ..tasks import get_processors, get_tasks
        from ..threadhandlers import LeftOverJobsProcessor, RefreshProcessor

        thread_ids = []

        for task in get_tasks():
            thread_ids.append(task[1].__name__)

        return thread_ids

    def is_system_healthy():
        status_is_valid = True

        c = ConfigurationEntry.get()
        if c.background_tasks:
            # I assume at least one check should be made
            if SystemOperation.get_last_internet_check():
                delta = (
                    DateUtils.get_datetime_now_utc()
                    - SystemOperation.get_last_internet_check()
                )

                hours_limit = 3600  # TODO hardcoded refresh task should be running more often than 1 hour?

                if delta.total_seconds() > hours_limit:
                    status_is_valid = False

            hours_limit = 3 * 3600  # processing task can push things to git

            thread_ids = SystemOperation.get_thread_ids()

            for thread_id in thread_ids:
                date = SystemOperation.get_last_thread_signal(thread_id)
                if not date:
                    status_is_valid = False
                    break

                delta = DateUtils.get_datetime_now_utc() - date

                if delta.total_seconds() > hours_limit:
                    status_is_valid = False
                    break

        return status_is_valid


class UserConfig(models.Model):
    # TODO move this to relation towards Users
    username = models.CharField(max_length=500, unique=True)
    display_style = models.CharField(
        max_length=500, null=True, default="style-light", choices=STYLE_TYPES
    )
    display_type = models.CharField(
        max_length=500,
        null=True,
        default="standard",
        choices=ConfigurationEntry.DISPLAY_TYPE_CHOICES,
    )
    show_icons = models.BooleanField(default=True)
    thumbnails_as_icons = models.BooleanField(default=True)
    small_icons = models.BooleanField(default=True)
    links_per_page = models.IntegerField(default=100)
    karma = models.IntegerField(default=0)
    birth_date = models.DateField(null=True, help_text="Format: 2024-03-28")
    links_per_page = models.IntegerField(default=100)
    sources_per_page = models.IntegerField(default=100)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_user_configs",
        null=True,
    )

    def get(user=None):
        """
        This is used if no request is specified. Use configured by admin setup.
        """
        if user and user.is_authenticated:
            confs = UserConfig.objects.filter(user__id=user.id)
            if confs.count() != 0:
                return confs[0]

        # create some user from settings

        config = ConfigurationEntry.get()
        return UserConfig(
            display_style=config.display_style,
            display_type=config.display_type,
            show_icons=config.show_icons,
            thumbnails_as_icons=config.thumbnails_as_icons,
            links_per_page=config.links_per_page,
            sources_per_page=config.sources_per_page,
        )

    def get_or_create(input_user):
        """
        This is used if no request is specified. Use configured by admin setup.
        """
        if not input_user.is_authenticated:
            config = ConfigurationEntry.get()
            return UserConfig(
                display_style=config.display_style,
                display_type=config.display_type,
                show_icons=config.show_icons,
                thumbnails_as_icons=config.thumbnails_as_icons,
                links_per_page=config.links_per_page,
                sources_per_page=config.sources_per_page,
            )

        users = UserConfig.objects.filter(user=input_user)
        if not users.exists():
            user = UserConfig.objects.create(username=input_user.username, user=input_user)
            return user
        return users[0]

    def save(self, *args, **kwargs):
        config = ConfigurationEntry.get()

        # Trim the input string to fit within max_length
        if self.links_per_page > config.max_links_per_page:
            self.links_per_page = config.max_links_per_page

        if self.sources_per_page > config.max_sources_per_page:
            self.sources_per_page = config.max_sources_per_page

        super().save(*args, **kwargs)

    def cleanup():
        configs = UserConfig.objects.filter(user__isnull=True)
        for uc in configs:
            us = User.objects.filter(username=uc.user)
            if us.count() > 0:
                uc.user = us[0]
                uc.save()

    def get_age(self):
        diff = relativedelta(date.today(), self.birth_date).years
        return diff


class AppLogging(models.Model):
    """
    info_text should be one liner.
    detail_text can be longer.
    """

    info_text = models.CharField(default="", max_length=2000)
    detail_text = models.CharField(
        blank=True, max_length=2000, help_text="Used to provide details about log event"
    )
    level = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=1000, null=True)

    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    NOTIFICATION = 60  # notifications for the user

    class Meta:
        ordering = ["-date", "level"]

    def get_local_time(self):
        from ..configuration import Configuration

        c = Configuration.get_object()
        return c.get_local_time(self.date)

    def create_entry(
        info_text, detail_text="", level=INFO, date=None, user=None, stack=False
    ):
        config = ConfigurationEntry.get()
        if level < config.logging_level:
            return

        if stack:
            stack_lines = traceback.format_stack()
            stack_string = "".join(stack_lines)
            # TODO - only 5 lines?

            if detail_text != "":
                detail_text += ". "
            detail_text += stack_string

        # TODO replace hardcoded values with something better
        LinkDatabase.info("AppLogging::{}:{}".format(level, info_text))

        AppLogging.cleanup_overflow()

        if len(info_text) > 1900:
            info_text = info_text[:1900]
        if len(detail_text) > 1900:
            detail_text = detail_text[:1900]

        AppLogging.objects.create(
            info_text=info_text,
            detail_text=detail_text,
            level=level,
            date=datetime.now(timezone("UTC")),
            user=user,
        )

    def info(info_text, detail_text="", user=None, stack=False):
        AppLogging.create_entry(
            info_text, detail_text=detail_text, level=AppLogging.INFO, stack=stack
        )

    def debug(info_text, detail_text="", user=None, stack=False):
        if stack:
            stack_lines = traceback.format_stack()
            stack_string = "".join(stack_lines)

            if detail_text != "":
                detail_text += ". "
            detail_text += stack_string

        LinkDatabase.info(info_text)
        if detail_text != "":
            LinkDatabase.info(detail_text)

    def warning(info_text, detail_text="", user=None, stack=False):
        AppLogging.create_entry(
            info_text, detail_text=detail_text, level=AppLogging.WARNING, stack=stack
        )

    def error(info_text, detail_text="", user=None, stack=False):
        AppLogging.create_entry(
            info_text, detail_text=detail_text, level=AppLogging.ERROR, stack=stack
        )

    def notify(info_text, detail_text="", user=None):
        AppLogging.create_entry(
            info_text, detail_text=detail_text, level=AppLogging.NOTIFICATION
        )

    def exc(exception_object, info_text=None, user=None):
        error_text = traceback.format_exc()
        print("Exception format")
        print(error_text)

        stack_lines = traceback.format_stack()
        stack_string = "".join(stack_lines)
        print("Stack:")
        print("".join(stack_lines))

        # only 5 lines!
        # stack_lines = stack_lines[-5:]
        # stack_string = "".join(stack_lines)

        if info_text:
            info_text += ". Exception:{}".format(str(exception_object))
            detail_text = "Data:\n{}\nStack:\n{}".format(error_text, stack_string)
        else:
            info_text = "{}".format(str(exception_object))
            detail_text = "Data:\n{}Stack:\n{}".format(error_text, stack_string)

        AppLogging.create_entry(
            info_text=info_text, detail_text=detail_text, level=AppLogging.ERROR
        )

    def save(self, *args, **kwargs):
        # Trim the input string to fit within max_length
        if len(self.info_text) > self._meta.get_field("info_text").max_length:
            self.info_text = self.info_text[
                : self._meta.get_field("info_text").max_length
            ]

        super().save(*args, **kwargs)

    def cleanup():
        AppLogging.remove_old_infos()

        obs = AppLogging.objects.filter(level=int(logging.INFO))
        if obs.exists():
            obs.delete()

    def cleanup_overflow():
        infos = AppLogging.objects.all().order_by("date")
        info_size = infos.count()
        if info_size > AppLogging.get_max_log_entries():
            index = 0
            for info in infos:
                info.delete()
                index += 1

                if info_size - index <= 1000:
                    return

    def get_max_log_entries():
        """
        TODO this should be configurable in the configuration
        """
        return 2000

    def truncate():
        AppLogging.objects.all().delete()

    def get_safe():
        return AppLogging.objects.all()[0:100]

    def remove_old_infos():
        try:
            date_range = DateUtils.get_days_range(3)
            while True:
                objs = AppLogging.objects.filter(date__lt=date_range[0])

                if not objs.exists():
                    break

                obj = objs[0]
                obj.delete()
        except Exception as e:
            LinkDatabase.info("Could not remove old persistant infos {}".format(e))

    def is_info(self):
        return self.level == AppLogging.INFO

    def is_warning(self):
        return self.level == AppLogging.WARNING

    def is_debug(self):
        return self.level == AppLogging.DEBUG

    def is_error(self):
        return self.level == AppLogging.ERROR

    def is_notification(self):
        return self.level == AppLogging.NOTIFICATION


class BackgroundJob(models.Model):
    JOB_PROCESS_SOURCE = "process-source"
    JOB_LINK_ADD = "link-add"
    JOB_LINK_SAVE = "link-save"
    JOB_LINK_UPDATE_DATA = "link-update-data"
    JOB_LINK_RESET_DATA = "link-reset-data"
    JOB_LINK_RESET_LOCAL_DATA = "link-reset-local-data"
    JOB_LINK_DOWNLOAD = "link-download"
    JOB_LINK_DOWNLOAD_MUSIC = "download-music"
    JOB_LINK_DOWNLOAD_VIDEO = "download-video"
    JOB_DOWNLOAD_FILE = "download-file"  # TODO stor file, should mention DB
    JOB_LINK_SCAN = "link-scan"
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
    JOB_RUN_RULE = "run-rule"
    JOB_CHECK_DOMAINS = "check-domains"

    # fmt: off
    JOB_CHOICES = (
        (JOB_PROCESS_SOURCE, JOB_PROCESS_SOURCE,),              # for RSS sources it checks if there are new data
        (JOB_LINK_ADD, JOB_LINK_ADD,),                          # adds link using default properties, may contain link map properties in the map
        (JOB_LINK_SAVE, JOB_LINK_SAVE,),                        # link is saved using thirdparty pages (archive.org)
        (JOB_LINK_UPDATE_DATA, JOB_LINK_UPDATE_DATA),           # fetches data from the internet, updates what is missing, updates page rating
        (JOB_LINK_RESET_DATA, JOB_LINK_RESET_DATA,),            # fetches data from the internet, replaces data, updates page rating
        (JOB_LINK_RESET_LOCAL_DATA, JOB_LINK_RESET_LOCAL_DATA,),# recalculates page rating
        (JOB_LINK_DOWNLOAD, JOB_LINK_DOWNLOAD),                 # link is downloaded using wget
        (JOB_LINK_DOWNLOAD_MUSIC, JOB_LINK_DOWNLOAD_MUSIC),     #
        (JOB_LINK_DOWNLOAD_VIDEO, JOB_LINK_DOWNLOAD_VIDEO),     #
        (JOB_DOWNLOAD_FILE, JOB_DOWNLOAD_FILE),     #
        (JOB_LINK_SCAN, JOB_LINK_SCAN,),
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
        (JOB_CHECK_DOMAINS, JOB_CHECK_DOMAINS),
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

    class Meta:
        ordering = [
            "-enabled",
            "priority",
            "date_created",
            "job",
            "pk",
            "subject",
            "errors",
            ]


class AppLoggingController(object):
    """
    Implementation of weblogger that only prints to std out
    """

    def info(self, info_text, detail_text="", user=None, stack=False):
        AppLogging.info(info_text, detail_text, user, stack)

    def debug(self, info_text, detail_text="", user=None, stack=False):
        AppLogging.debug(info_text, detail_text, user, stack)

    def warning(self, info_text, detail_text="", user=None, stack=False):
        AppLogging.warning(info_text, detail_text, user, stack)

    def error(self, info_text, detail_text="", user=None, stack=False):
        AppLogging.error(info_text, detail_text, user, stack)

    def notify(self, info_text, detail_text="", user=None):
        AppLogging.notify(info_text, detail_text, user )

    def exc(self, exception_object, info_text=None, user=None):
        AppLogging.exc(exception_object, info_text, user)
