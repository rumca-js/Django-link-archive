import time
from datetime import timedelta
import base64

from django.db import models
from django.db.models import Q, F

from ..webtools import (
    RemoteServer,
)
from utils.dateutils import DateUtils

from ..models import (
    BaseLinkDataController,
    AppLogging,
    EntryRules,
)
from ..controllers import LinkDataController, EntryWrapper, EntryPageCrawler
from ..configuration import Configuration
from ..apps import LinkDatabase
from .entrywrapper import EntryWrapper
from .entrycleanup import EntryCleanup
from .entriesutils import add_all_domains
from .backgroundjob import BackgroundJobController
from .domains import DomainsController


class EntryUpdater(object):
    def __init__(self, entry, browser=None):
        self.entry = entry
        self.browser = browser

    def is_entry_changed(self, all_properties):
        entry = self.entry

        if not all_properties:
            return True

        request_server = RemoteServer("https://")

        response = request_server.read_properties_section("Response", all_properties)

        if "Last-Modified" in response:
            last_modified_date = response["Last-Modified"]
            if last_modified_date:
                if not entry.date_last_modified:
                    return True

                last_modified_date = DateUtils.parse_datetime(last_modified_date)

                if last_modified_date > entry.date_last_modified:
                    return True

                return False

        body_hash = response["body_hash"]
        if body_hash:
            if not entry.body_hash:
                return True

            body_hash = base64.b64decode(body_hash)

            if entry.body_hash == body_hash:
                return False

            return True

        contents_hash = response["hash"]
        if contents_hash:
            if not entry.contents_hash:
                return True

            contents_hash = base64.b64decode(contents_hash)

            if entry.contents_hash == contents_hash:
                return False

            return True

        return True

    def update_entry_common_fields(self, all_properties):
        entry = self.entry

        request_server = RemoteServer("https://")

        response = request_server.read_properties_section("Response", all_properties)
        properties = request_server.read_properties_section(
            "Properties", all_properties
        )

        if response:
            if "Last-Modified" in response and response["Last-Modified"]:
                last_modified_date = DateUtils.parse_datetime(response["Last-Modified"])
                entry.date_last_modified = last_modified_date
            else:
                entry.date_last_modified = DateUtils.get_datetime_now_utc()
            if "status_code" in response:
                entry.status_code = response["status_code"]
            if "body_hash" in response:
                body_hash = base64.b64decode(response["body_hash"])
                entry.body_hash = body_hash
            if "hash" in response:
                contents_hash = base64.b64decode(response["hash"])
                entry.contents_hash = contents_hash

        if properties:
            if "page_rating" in properties:
                entry.page_rating_contents = int(properties["page_rating"])
            date_published = properties.get("date_published")
            try:
                date_published = DateUtils.parse_datetime(date_published)
            except Exception as E:
                date_published = None

            if date_published:
                if not entry.date_published:
                    entry.date_published = date_published
                elif date_published < entry.date_published:
                    entry.date_published = date_published

        # if server says that entry was last modified in 2006, then it was present in 2006!
        if entry.date_last_modified:
            if (
                not entry.date_published
                or entry.date_last_modified < entry.date_published
            ):
                entry.date_published = entry.date_last_modified

        # if update date says that was published before, then it must have was published then
        if entry.date_published and entry.date_update_last:
            if entry.date_update_last < entry.date_published:
                entry.date_published = entry.date_update_last

        properties = {"title": entry.title, "description": entry.description}

        entry.save()

    def enhance_entry_location(self):
        if not self.entry:
            return

        EntryRules.check_all(self.entry)

        try:
            self.entry.refresh_from_db()
        except Exception as E:
            return

        w = EntryWrapper(entry=self.entry)
        w.evaluate() # moves to archive, deletes if time for it

        if w.entry is None:
            return

        try:
            self.entry.refresh_from_db()
        except Exception as E:
            AppLogging.error("After evaluation - removed")
            return

        if not w.is_current_entry_perfect():
            if w.entry.link.startswith("http"):
                w.check_https_http_availability()
                w.check_www_nonww_availability()

        # entry could have been moved to archive
        self.entry = w.entry

        config = Configuration.get_object().config_entry
        if config.enable_domain_support:
            DomainsController.add(self.entry.link)

        if config.enable_crawling and config.auto_crawl_sources:
            if config.accept_domain_links:
                add_all_domains(self.entry.link)

    def update_data(self):
        from ..pluginurl import EntryUrlInterface
        from ..pluginurl import UrlHandlerEx

        """
        Fetches new information about page, and uses valid fields to set this object,
        but only if current field is not set

         - status code and page rating is update always
         - title and description could have been set manually, we do not want to change that
         - some other fields should be set only if present in props
        """
        if not self.entry:
            return

        self.enhance_entry_location()

        try:
            self.entry.refresh_from_db()
        except Exception as E:
            return

        entry = self.entry

        url = UrlHandlerEx(self.entry.link)
        url.get_response()

        if url.is_server_error():
            raise IOError(f"{self.entry.link}: Crawling server error")

        if url.is_blocked():
            if entry.is_removable():
                AppLogging.warning(f"Url:{self.entry.link} Removing link. Blocked by a rule.")
                entry.delete()
                return

        props = None
        url_interface = None

        entry_changed = self.is_entry_changed(url.all_properties)

        entry.date_update_last = DateUtils.get_datetime_now_utc()
        entry.save()

        if not entry_changed:
            return

        self.update_entry_common_fields(url.all_properties)

        if url.is_valid():
            url_interface = EntryUrlInterface(entry.link, browser=self.browser, handler=url)
            props = url_interface.get_props()

            # we may not support update for some types. PDFs, other resources on the web
            if props and len(props) > 0:
                title = props.get("title")
                if title:
                    if not entry.title:
                        entry.title = title

                description = props.get("description")
                if description:
                    if not entry.description:
                        entry.description = description

                thumbnail = props.get("thumbnail")
                if thumbnail:
                    # always update
                    entry.thumbnail = thumbnail

                language = props.get("language")
                if language:
                    if not entry.language:
                        entry.language = language

                date_published = props.get("date_published")
                if date_published:
                    if not entry.date_published:
                        entry.date_published = date_published

            if entry.date_dead_since:
                entry.date_dead_since = None

            entry.save()

        self.reset_local_data()

        if url.is_invalid():
            self.handle_invalid_response(url)
        elif url.is_valid():
            self.perform_additional_update_elements(url)
        # else - when crawler exception

    def reset_data(self):
        from ..pluginurl import EntryUrlInterface
        from ..pluginurl import UrlHandlerEx

        if not self.entry:
            return

        self.enhance_entry_location()

        try:
            self.entry.refresh_from_db()
        except Exception as E:
            return

        entry = self.entry

        url = UrlHandlerEx(self.entry.link)
        url.get_response()

        if url.is_server_error():
            raise IOError(f"{self.entry.link}: Crawling server error")

        if url.is_blocked():
            if entry.is_removable():
                AppLogging.warning(f"Url:{self.entry.link} Removing link. Blocked by a rule.")
                entry.delete()
                return

        props = None
        url_interface = None

        entry_changed = self.is_entry_changed(url.all_properties)

        entry.date_update_last = DateUtils.get_datetime_now_utc()
        entry.save()

        if not entry_changed:
            return

        self.update_entry_common_fields(url.all_properties)

        if url.is_valid():
            url_interface = EntryUrlInterface(entry.link, browser=self.browser, handler=url)
            props = url_interface.get_props()

            # we may not support update for some types. PDFs, other resources on the web
            if props and len(props) > 0:
                title = props.get("title")
                if title:
                    entry.title = title

                description = props.get("description")
                if description:
                    entry.description = description

                thumbnail = props.get("thumbnail")
                if thumbnail:
                    entry.thumbnail = thumbnail

                language = props.get("language")
                if language:
                    entry.language = language

                date_published = props.get("date_published")
                if date_published:
                    if not entry.date_published:
                        entry.date_published = date_published

            if entry.date_dead_since is not None:
                entry.date_dead_since = None

            entry.save()

        self.reset_local_data()

        if url.is_invalid():
            self.handle_invalid_response(url)
        elif url.is_valid():
            self.perform_additional_update_elements(url)
        # else - when crawler exception

    def perform_additional_update_elements(self, url):
        entry = self.entry

        c = Configuration.get_object()
        config = c.config_entry

        if config.auto_scan_updated_entries:
            BackgroundJobController.link_scan(entry=self.entry)

        if config.keep_social_data:
            BackgroundJobController.link_download_social_data(entry)

        self.add_links_from_url(entry, url)

        self.store_thumbnail(entry)

    def store_thumbnail(self, entry):
        if entry.page_rating_votes > 0:  # TODO should that be configurable?
            from .modelfiles import ModelFilesBuilder

            c = Configuration.get_object()
            config = c.config_entry
            if config.auto_store_thumbnails:
                ModelFilesBuilder().build(file_name=entry.thumbnail)

    def add_links_from_url(self, entry, url):
        properties = url.all_properties

        if not properties:
            return

        scanner = EntryPageCrawler(url=entry.link, entry=entry, properties=properties)
        scanner.run()

    def reset_local_data(self):
        self.update_calculated_vote()

    def calculate_vote(self):
        """
        TODO use median instead of avarage
        """
        if not self.entry.is_taggable():
            return 0

        votes = self.entry.votes.all()
        count = votes.count()
        if count == 0:
            return 0

        sum_num = 0
        for vote in votes:
            sum_num += vote.vote

        return sum_num / count

    def get_visits(self):
        from ..models import UserEntryVisitHistory

        if self.entry.is_archive_entry():
            return 0

        visits = UserEntryVisitHistory.objects.filter(entry=self.entry)

        sum_num = 0
        for visit in visits:
            sum_num += visit.visits

        return sum_num

    def update_calculated_vote(self):
        """
        Warning: Do not change page rating range. Should be always -100..100
        The impact of factors can change ratings only in that range
        """
        entry = self.entry
        entry.page_rating_votes = self.calculate_vote()
        entry.page_rating_visits = self.get_visits()

        are_tags = 0
        if not entry.is_archive_entry():
            tags = entry.tags.all()
            if tags.exists():
                are_tags = 1

        # votes are twice as important as contents
        page_rating = (
            (2 * entry.page_rating_votes) + entry.page_rating_contents
        ) + are_tags * 10
        max_page_rating = 2 * 100 + 100 + 10

        # rating in percentage. Range -100..100
        entry.page_rating = page_rating * 100 / max_page_rating

        entry.save()

    def handle_invalid_response(self, url):
        entry = self.entry

        entry.page_rating = 0

        if not entry.date_dead_since:
            AppLogging.error(
                "Cannot access link:{} entry id:{}".format(entry.link, entry.id)
            )
            entry.date_dead_since = DateUtils.get_datetime_now_utc()
            entry.save()

        cleanup = EntryCleanup(entry)

        link = self.entry.link
        date = self.entry.date_dead_since

        if cleanup.is_delete_time():
            if self.entry.is_removable():
                self.entry.delete()

                AppLogging.notify(
                    "Removed entry <a href='{}'>{}</a>. It was dead since {}.".format(
                        link, link, date
                    )
                )
                return

        entry.page_rating_contents = 0

        if url.all_properties:
            server = RemoteServer("")
            response = server.read_properties_section(
                "Response", url.all_properties
            )
            if response:
                entry.status_code = response["status_code"]
            else:
                entry.status_code = BaseLinkDataController.STATUS_DEAD
        else:
            entry.status_code = BaseLinkDataController.STATUS_DEAD
        entry.save()


class EntriesUpdater(object):
    def get_entries_to_update(self, max_number_of_entries):
        """
        @note
        Normal entries are checked with interval days_to_check_std_entries
        Dead entries are checked with interval days_to_check_stale_entries
        """
        config = Configuration.get_object().config_entry

        if config.days_to_check_std_entries == 0:
            return

        date_to_check_std = DateUtils.get_datetime_now_utc() - timedelta(
            days=config.days_to_check_std_entries
        )
        date_to_check_stale = DateUtils.get_datetime_now_utc() - timedelta(
            days=config.days_to_check_stale_entries
        )

        condition_days_to_check_std = Q(date_update_last__lt=date_to_check_std)
        condition_days_to_check_stale = Q(date_update_last__lt=date_to_check_stale)

        condition_not_dead = Q(date_dead_since__isnull=False)
        condition_dead = Q(date_dead_since__isnull=True)

        condition_update_null = Q(date_update_last__isnull=True)

        entries = LinkDataController.objects.filter(
            condition_update_null
            | (condition_not_dead & condition_days_to_check_std)
            | (condition_dead & condition_days_to_check_stale)
        ).order_by("date_update_last", "link")[:max_number_of_entries]

        return entries
