import logging
import traceback
from pathlib import Path
import os
from pytz import timezone
from datetime import datetime, date, timedelta, time
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.templatetags.static import static

from utils.dateutils import DateUtils

from ..apps import LinkDatabase


def batch_remove(model, query, batch_size):
    while True:
        batch_ids = list(query.values_list("id", flat=True)[:batch_size])
        if not batch_ids:
            break

        model.objects.filter(id__in=batch_is).delete()


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
        (ACCESS_TYPE_ALL, ACCESS_TYPE_ALL),
        (ACCESS_TYPE_LOGGED, ACCESS_TYPE_LOGGED),
        (ACCESS_TYPE_STAFF, ACCESS_TYPE_STAFF),
        (ACCESS_TYPE_OWNER, ACCESS_TYPE_OWNER),
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

    SEARCH_BUTTON_ALL = "search-button-all"
    SEARCH_BUTTON_RECENT = "search-button-recent"
    SEARCH_BUTTON_GLOBAL_BOOKMARKS = "search-button-global-bookmarks"
    SEARCH_BUTTON_USER_BOOKMARKS = "search-button-user-bookmarks"

    SEARCH_BUTTONS = (
        (SEARCH_BUTTON_ALL, SEARCH_BUTTON_ALL),
        (SEARCH_BUTTON_RECENT, SEARCH_BUTTON_RECENT),
        (SEARCH_BUTTON_GLOBAL_BOOKMARKS, SEARCH_BUTTON_GLOBAL_BOOKMARKS),
        (SEARCH_BUTTON_USER_BOOKMARKS, SEARCH_BUTTON_USER_BOOKMARKS),
    )

    CONFIGURATION_NEWS = "News"
    CONFIGURATION_GALLERY = "Gallery"
    CONFIGURATION_SEARCH_ENGINE = "Search Engine"

    CONFIGURATION_TYPES = (
       (CONFIGURATION_NEWS, CONFIGURATION_NEWS),
       (CONFIGURATION_GALLERY, CONFIGURATION_GALLERY),
       (CONFIGURATION_SEARCH_ENGINE, CONFIGURATION_SEARCH_ENGINE),
    )

    # fmt: on
    instance_title = models.CharField(
        default="Personal Link Database",
        max_length=500,
        help_text="Title of the application instance.",
    )

    instance_description = models.CharField(
        default="Personal Link Database. May work as link aggregator, may link as YouTube subscription filter.",
        max_length=500,
        help_text="Description of the application instance.",
    )

    instance_internet_location = models.CharField(
        blank=True,
        max_length=200,
        help_text="URL where the instance is hosted. For example, https://my-domain.com/apps/rsshistory/",
    )

    favicon_internet_url = models.CharField(
        blank=True,
        max_length=200,
        help_text="URL of the instance's favicon. For example, https://my-domain.com/static/icons/favicon.ico",
    )

    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_admin_user",
        null=True,
        blank=True,
        help_text=(
            "Admin user that is used to perform actions, be it link adding, tagging"
        )
    )

    view_access_type = models.CharField(
        max_length=100,
        null=False,
        choices=ACCESS_TYPES,
        default=ACCESS_TYPE_ALL,
        help_text=(
            "Defines who can view the contents of the application. "
            "'All' allows anyone, 'Logged' restricts to logged-in users, and 'Owner' makes it private to the owner."
        ),
    )

    download_access_type = models.CharField(
        max_length=100,
        null=False,
        choices=ACCESS_TYPES,
        default=ACCESS_TYPE_LOGGED,
        help_text="Defines the access level required to download items.",
    )

    add_access_type = models.CharField(
        max_length=100,
        null=False,
        choices=ACCESS_TYPES,
        default=ACCESS_TYPE_LOGGED,
        help_text="Defines the access level required to add entries to the database.",
    )

    logging_level = models.IntegerField(
        default=logging.WARNING,
        choices=[
            (logging.DEBUG, "Debug"),
            (logging.INFO, "Info"),
            (logging.WARNING, "Warning"),
            (logging.ERROR, "Error"),
            (logging.CRITICAL, "Critical"),
        ],
        help_text="Specifies the logging level for the application.",
    )

    initialized = models.BooleanField(
        default=False,
        help_text="Indicates whether the application instance has been initialized.",
    )

    initialization_type = models.CharField(
        default=CONFIGURATION_NEWS,
        choices=CONFIGURATION_TYPES,
        max_length=200,
        blank=True,
        help_text="Type of initialization, be it news, gallery.",
    )

    enable_background_jobs = models.BooleanField(
        default=True,
        help_text="If enabled other task is responsible for job processing. If disabled background jobs are immediately processed by the current thread.",
    )

    block_job_queue = models.BooleanField(
        default=False,
        help_text="Allows to temporarily block job queues, jobs will not be created",
    )

    use_internal_scripts = models.BooleanField(
        default=False,
        help_text=(
            "If enabled, internal JavaScript and CSS files will be used. "
            "Otherwise, external libraries like jQuery will be loaded from CDNs."
        ),
    )

    cleanup_time = models.TimeField(
        default=time(0, 0), help_text="Time at which cleanup is performed"
    )

    # TODO change null to blank
    data_import_path = models.CharField(
        default="../data/imports",
        max_length=2000,
        null=True,
        help_text="Path to the directory for data imports.",
    )
    # TODO change null to blank
    data_export_path = models.CharField(
        default="../data/exports",
        max_length=2000,
        null=True,
        help_text="Path to the directory for data exports.",
    )
    # TODO change null to blank
    download_path = models.CharField(
        max_length=2000,
        null=True,
        blank=True,
        help_text="Path to the directory where downloaded files are stored.",
    )

    auto_store_thumbnails = models.BooleanField(
        default=False,
        help_text=(
            "If enabled, thumbnails will be stored automatically. This feature is available "
            "only when file support is enabled."
        ),
    )

    thread_memory_threshold = models.IntegerField(
        default=500,
        help_text="Unit [MB]. Virtual memory threshold for threads. If memory threshold is breached thread leaves.",
    )

    # features

    enable_keyword_support = models.BooleanField(
        default=True, help_text="Enable keyword feature support"
    )

    enable_domain_support = models.BooleanField(
        default=True,
        help_text="Enable domain feature support. Creates additional domain objects when a new entry is add.",
    )

    # TODO discuss what it does in help_text
    enable_file_support = models.BooleanField(
        default=False, help_text="Enable file feature support"
    )

    enable_link_archiving = models.BooleanField(
        default=False, help_text="Enable archiving of links using archive.org."
    )

    enable_source_archiving = models.BooleanField(
        default=False, help_text="Enable archiving of sources using archive.org."
    )

    enable_crawling = models.BooleanField(
        default=False,
        help_text="Automatically crawls links in sources. Finds links in RSS sources and adds them."
    )

    keep_social_data = models.BooleanField(
        default=True,
        help_text="Keep link social data in the database.",
    )

    # database link contents

    accept_dead_links = models.BooleanField(
        default=False,
        help_text="Allow adding inactive or broken links to the database.",
    )

    accept_ip_links = models.BooleanField(
        default=False,
        help_text="Allow adding links that use IP addresses, such as //127.0.0.1/my/directory.",
    )

    accept_domain_links = models.BooleanField(
        default=True, help_text="Allow adding links that are domains to the system."
    )

    accept_non_domain_links = models.BooleanField(
        default=True, help_text="Allow adding links that are not domains to the system."
    )

    auto_crawl_sources = models.BooleanField(
        default=False,
        help_text="Crawling. Automatically finds links from sources (domain, links in RSS)."
    )

    auto_scan_new_entries = models.BooleanField(
        default=False,
        help_text="Crawling. Scans new entry for new links.",
    )

    auto_scan_updated_entries = models.BooleanField(
        default=False,
        help_text="Crawling. Scans updated entries for new links.",
    )

    # TODO rename to merge_data_for_new_entries
    new_entries_merge_data = models.BooleanField(
        default=False,
        help_text="New entries (for example from RSS) will be updated with Internet data.",
    )

    # TODO rename to use_clean_data_for_new_entries
    new_entries_use_clean_data = models.BooleanField(
        default=False,
        help_text="New entries will use data fresh from Internet crawling, not from source",
    )

    new_entries_fetch_social_data = models.BooleanField(
        default=False,
        help_text="New entries will fetch social data",
    )

    entry_update_via_internet = models.BooleanField(
        default=True,
        help_text="Use the Internet to check the status of entries during updates. Otherwise entriy data will not be fetched by Internet",
    )

    log_remove_entries = models.BooleanField(
        default=False,
        help_text="If true, automatic entry remove operations will be logged.",
    )

    auto_create_sources = models.BooleanField(
        default=False,
        help_text="Automatically add newly found sources to the system.",
    )

    default_source_state = models.BooleanField(
        default=False, help_text="Set the default state of newly added sources."
    )

    prefer_https_links = models.BooleanField(
        default=True,
        help_text="Prefer HTTPS links. If updates reveal an HTTPS version, replace HTTP links with it.",
    )

    prefer_non_www_links = models.BooleanField(
        default=False,
        help_text="Prefer non-www links. Replace www links with cleaner versions if available during updates.",
    )

    # updates

    sources_refresh_period = models.IntegerField(
        default=3600,
        help_text="Unit [s]. Defines how often sources are checked for data.",
    )

    days_to_move_to_archive = models.IntegerField(
        default=50,
        help_text="Number of days after which entries are moved to archive. Disabled if 0.",
    )

    days_to_remove_links = models.IntegerField(
        default=100,
        help_text="Number of days after which links are removed. Useful for RSS clients. Disabled if 0.",
    )

    days_to_remove_stale_entries = models.IntegerField(
        default=35, help_text="Number of days after which inactive entries are removed."
    )

    days_to_check_std_entries = models.IntegerField(
        default=35,
        help_text="Number of days after which standard entries are checked for status.",
    )

    days_to_check_stale_entries = models.IntegerField(
        default=35,
        help_text="Number of days after which inactive entries are checked for status.",
    )

    days_to_remove_social_data = models.IntegerField(
        default=5,
        help_text="Number of days after which social data are removed Disabled if 0.",
    )

    remove_entry_vote_threshold = models.IntegerField(
        default=1,
        help_text="Threshold for votes required to retain an entry. Disabled if set to 0.",
    )

    number_of_update_entries = models.IntegerField(
        default=1,
        help_text="Number of entries that will be updated during each refresh cycle.",
    )

    # Networking

    remote_webtools_server_location = models.CharField(
        blank=True,
        max_length=200,
        help_text="URL where the webtools server is located. If defined remote server is used for crawling.",
    )

    internet_status_test_url = models.CharField(
        default="https://google.com",
        max_length=2000,
        null=True,
        help_text="URL used to test internet connectivity. It will be pinged to verify internet access.",
    )

    # User settings

    track_user_actions = models.BooleanField(
        default=True,
        help_text="Track user actions, including search queries.",
    )

    track_user_searches = models.BooleanField(
        default=True,
        help_text="Enable or disable tracking of user searches.",
    )

    track_user_navigation = models.BooleanField(
        default=False,
        help_text="Enable or disable tracking of user navigation across pages (entry visits).",
    )

    max_user_entry_visit_history = models.IntegerField(
        default=5000,
        help_text="The maximum number of entry visit history. If set to 0, entry visit history is not cleared.",
    )

    max_number_of_user_search = models.IntegerField(
        default=700,
        help_text="The maximum number of searches stored in history. If set to 0, search history is not cleared.",
    )

    vote_min = models.IntegerField(
        default=-100, help_text="The minimum allowed vote value."
    )

    vote_max = models.IntegerField(
        default=100, help_text="The maximum allowed vote value."
    )

    number_of_comments_per_day = models.IntegerField(
        default=1,
        help_text="The maximum number of comments a user can post per day to maintain community culture.",
    )

    # display

    time_zone = models.CharField(
        max_length=50,
        default="UTC",
        help_text="Specify the time zone. Example: Europe/Warsaw. A list of time zones can be found at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.",
    )

    display_style = models.CharField(
        max_length=500,
        null=True,
        default=DISPLAY_STYLE_LIGHT,
        choices=STYLE_TYPES,
        help_text="Defines the display style for users who are not logged in.",
    )
    display_type = models.CharField(
        max_length=500,
        null=True,
        default=DISPLAY_TYPE_STANDARD,
        choices=DISPLAY_TYPE_CHOICES,
        help_text="Defines the display type for users who are not logged in.",
    )
    show_icons = models.BooleanField(
        default=True,
        help_text="Whether to display icons for users who are not logged in.",
    )
    thumbnails_as_icons = models.BooleanField(
        default=True,
        help_text="If false, source favicons are used as thumbnails for users who are not logged in.",
    )
    small_icons = models.BooleanField(
        default=True,
        help_text="Whether to use small icons for users who are not logged in.",
    )
    local_icons = models.BooleanField(
        default=False,
        help_text="If true, only locally stored icons are displayed for users who are not logged in.",
    )

    links_per_page = models.IntegerField(
        default=100,
        help_text="The number of links displayed per page for users who are not logged in.",
    )
    sources_per_page = models.IntegerField(
        default=100,
        help_text="The number of sources displayed per page for users who are not logged in.",
    )

    max_links_per_page = models.IntegerField(
        default=100,
        help_text="The maximum number of links that can be displayed per page.",
    )
    max_sources_per_page = models.IntegerField(
        default=100,
        help_text="The maximum number of sources that can be displayed per page.",
    )
    max_number_of_related_links = models.IntegerField(
        default=30,
        help_text="The maximum number of related links displayed in the 'entry detail' view.",
    )

    entries_visit_alpha = models.FloatField(
        default=0.6,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Alpha of visited entries.",
    )

    entries_dead_alpha = models.FloatField(
        default=0.6,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Alpha of dead entries.",
    )

    debug_mode = models.BooleanField(
        default=False, help_text="Enable debug mode to see errors more clearly."
    )

    def get():
        """
        Most probably should not be used directly. Should be cached in application
        """
        confs = ConfigurationEntry.objects.all()
        if not confs.exists():
            return ConfigurationEntry.objects.create()
        else:
            return confs[0]

    def get_main_directory(self):
        file_path = os.path.realpath(__file__)
        full_path = Path(file_path)
        main_directory = full_path.parents[2]
        return main_directory

    def get_export_path_abs(self):
        main_directory = self.get_main_directory()
        return main_directory / self.data_export_path

    def get_import_path_abs(self):
        main_directory = self.get_main_directory()
        return main_directory / self.data_import_path

    def get_entries_order_by(self):
        """
        @note valid example "-date_published, -page_rating"
        @result tuple of order bies
        """
        input_string = self.entries_order_by
        delimiter = ","
        result_list = [item.strip() for item in input_string.split(delimiter)]
        return result_list

    def get_download_path(self):
        if self.download_path:
            return self.download_path

        if self.data_export_path:
            return self.data_export_path

    def save(self, *args, **kwargs):
        """
        Fix errors here
        """

        main_directory = self.get_main_directory()
        export_path = main_directory / self.data_export_path
        if not export_path.exists():
            try:
                export_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                self.data_export_path = None

        import_path = main_directory / self.data_import_path
        if not import_path.exists():
            try:
                import_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                self.data_import_path = None

        try:
            tzn = timezone(self.time_zone)
        except Exception as E:
            self.time_zone = "UTC"

        super().save(*args, **kwargs)


class SystemOperation(models.Model):
    CHECK_TYPE_INTERNET = "Internet"
    CHECK_TYPE_CRAWLING_SERVER = "CrawlingServer"

    thread_id = models.CharField(
        blank=True,
        help_text="Thread ID",
        max_length=100,
    )

    date_created = models.DateTimeField(auto_now_add=True, null=True)

    check_type = models.CharField(
        max_length=50,
        blank=True,
    )

    status = models.BooleanField(
        default=True,
        help_text="Is connection OK",
    )

    class Meta:
        ordering = ["-date_created"]

    def add_by_thread(thread_id, check_type="", status=True):
        # delete all entries without internet check
        all_entries = SystemOperation.objects.filter(
            thread_id=thread_id,
            check_type="",
        )
        all_entries.delete()

        # leave one entry with time check
        all_entries = SystemOperation.objects.filter(
            thread_id=thread_id, check_type=check_type
        )
        if all_entries.exists() and all_entries.count() > 1:
            entries = all_entries[1:]
            for entry in entries:
                entry.delete()

        SystemOperation.objects.create(
            thread_id=thread_id,
            check_type=check_type,
            status=status,
        )


class UserConfig(models.Model):
    # TODO move this to relation towards Users
    username = models.CharField(max_length=500, unique=True)
    display_style = models.CharField(
        max_length=500, null=True, default="style-light", choices=STYLE_TYPES
    )
    display_type = models.CharField(
        max_length=500,
        null=True,
        default=ConfigurationEntry.DISPLAY_TYPE_STANDARD,
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
    debug_mode = models.BooleanField(
        default=False, help_text="Enable debug mode to see errors more clearly."
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_user_configs",
        null=True,
    )

    def get_config_user():
        config = ConfigurationEntry.get()
        return UserConfig(
            display_style=config.display_style,
            display_type=config.display_type,
            show_icons=config.show_icons,
            thumbnails_as_icons=config.thumbnails_as_icons,
            links_per_page=config.links_per_page,
            sources_per_page=config.sources_per_page,
        )

    def get(input_user=None):
        """
        This is used if no request is specified. Use configured by admin setup.
        """
        if input_user and input_user.is_authenticated:
            confs = UserConfig.objects.filter(user__id=input_user.id)
            if confs.exists():
                return confs[0]

        # create some user from settings

        return UserConfig.get_config_user()

    def get_or_create(input_user):
        """
        @param input_user User Object

        This is used if no request is specified. Use configured by admin setup.
        """
        if not input_user.is_authenticated:
            return UserConfig.get_config_user()

        user_configs = UserConfig.objects.filter(user=input_user)

        if not user_configs.exists():
            user_configs = UserConfig.objects.filter(username=input_user.username)
            if user_configs.exists():
                user_config = user_configs[0]
            else:
                user_config = UserConfig.get_config_user()

            user_config.username = input_user.username
            user_config.user = input_user
            user_config.save()

            return user_config

        return user_configs[0]

    def save(self, *args, **kwargs):
        config = ConfigurationEntry.get()

        # Trim the input string to fit within max_length
        if self.links_per_page > config.max_links_per_page:
            self.links_per_page = config.max_links_per_page

        if self.sources_per_page > config.max_sources_per_page:
            self.sources_per_page = config.max_sources_per_page

        super().save(*args, **kwargs)

    def cleanup(cfg=None):
        configs = UserConfig.objects.filter(user__isnull=True)
        for uc in configs:
            us = User.objects.filter(username=uc.user)
            if us.exists():
                uc.user = us[0]
                uc.save()

    def get_age(self):
        diff = relativedelta(date.today(), self.birth_date).years
        return diff

    def is_authenticated(self):
        if not self.user:
            return False

        return self.user.is_authenticated

    def can_download(self):
        config = ConfigurationEntry.get()
        if not self.user or not self.user.is_authenticated:
            return False

        if (
            self.user.is_authenticated
            and config.download_access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
        ):
            return True
        if self.user.is_staff:
            return True

        return False

    def can_add(self):
        config = ConfigurationEntry.get()
        if not self.user or not self.user.is_authenticated:
            return False

        if (
            self.user.is_authenticated
            and config.add_access_type == ConfigurationEntry.ACCESS_TYPE_LOGGED
        ):
            return True
        if self.user.is_staff:
            return True

        return False


class AppLogging(models.Model):
    """
    info_text should be one liner.
    detail_text can be longer.
    """

    info_text = models.CharField(default="", max_length=2000)
    detail_text = models.CharField(
        blank=True, max_length=3000, help_text="Used to provide details about log event"
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
            # AppLogging.debug(info_text = info_text, detail_text = detail_text)
            return

        if stack:
            stack_lines = traceback.format_stack()
            stack_string = "".join(stack_lines)
            # TODO - only 5 lines?

            if detail_text != "":
                detail_text += ". "
            detail_text += stack_string

        if detail_text and detail_text != "":
            LinkDatabase.info(
                "AppLogging::{}:{}\n{}".format(level, info_text, detail_text)
            )
        else:
            LinkDatabase.info("AppLogging::{}:{}".format(level, info_text))

        AppLogging.cleanup_overflow()

        # TODO replace hardcoded values with something better
        if len(info_text) > 1900:
            info_text = info_text[:1900]
        if len(detail_text) > 2900:
            detail_text = detail_text[:2900]

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

    def cleanup(cfg=None):
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
        date_range = DateUtils.get_days_range(3)
        index = 0

        while True:
            objs = AppLogging.objects.filter(date__lt=date_range[0])

            if not objs.exists():
                break

            obj = objs[0]
            obj.delete()

            index += 1
            if index > 2000:
                print("AppLogging:remove_old_infos overflow")
                return

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

    def __str__(self):
        return "Date:{}\tLevel:{}\tInfo:{}\nDetail:{}".format(
            self.date, self.level, self.info_text, self.detail_text
        )


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
        AppLogging.notify(info_text, detail_text, user)

    def exc(self, exception_object, info_text=None, user=None):
        AppLogging.exc(exception_object, info_text, user)
