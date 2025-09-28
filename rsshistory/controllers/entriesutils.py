from datetime import timedelta
import traceback
import time
import ipaddress
import base64

from django.db import models
from django.urls import reverse
from django.db.models import Q, F

from ..webtools import (
    HttpRequestBuilder,
    ContentLinkParser,
    UrlLocation,
    UrlAgeModerator,
    RemoteServer,
)
from utils.dateutils import DateUtils

from ..models import (
    BaseLinkDataController,
    AppLogging,
    KeyWords,
    UserBookmarks,
    ModelFiles,
    ConfigurationEntry,
    EntryRules,
    SocialData,
)
from ..configuration import Configuration
from ..apps import LinkDatabase
from .entries import LinkDataController, ArchiveLinkDataController
from .backgroundjob import BackgroundJobController
from .domains import DomainsController
from .sources import SourceDataBuilder
from .sources import SourceDataController


class EntriesCleanup(object):
    def __init__(self, archive_cleanup=False, start_processing_time=None, limit_s=0):
        self.archive_cleanup = archive_cleanup

        if start_processing_time is None:
            self.start_processing_time = time.time()
        else:
            self.start_processing_time = start_processing_time

        if limit_s == 0:
            self.limit_s = 60 * 10  # 10 minutes
        else:
            self.limit_s = limit_s

    def cleanup(self, cfg=None):
        """
        We do not exit prematurely.

        Reason: if user has 200'000 links it make take a long time.
        During cleanup new links may become outdated.
        Cleanup may never end if we enter here for a few seconds only.
        Provide more queues, if you want such jobs to not clog queues.

        @return True if successful
        """
        AppLogging.debug("Cleanup - remove")

        if not self.cleanup_remove_entries():
            return False

        if not self.cleanup_entries__invalid_rules():
            return False

        if not self.archive_cleanup:
            if not self.move_old_links_to_archive():
                return False
        else:
            if not self.clean_archive():
                return False

        return True

    def cleanup_entries__invalid_rules(self):
        BATCH_SIZE = 1000

        rules = EntryRules.objects.filter(block=True, enabled=True)
        for rule in rules:
            urls = rule.get_rule_urls()

            for url in urls:
                if url != "":
                    entries = LinkDataController.objects.filter(link__icontains=url)
                    entries.delete()
                    # while entries.exists():
                    #    entries[:BATCH_SIZE].delete()

                    domains = DomainsController.objects.filter(domain__icontains=url)
                    domains.delete()
                    # while domains.exists():
                    #    domains[:BATCH_SIZE].delete()

        return True

    def cleanup_entries_with_ports(self):
        """
        This will only fix domains
        """
        invalid_domains = DomainsController.objects.filter(domain__contains=":")
        for invalid_domain in invalid_domains:
            invalid_domain_name = invalid_domain.domain
            wh = invalid_domain_name.find(":")
            if wh == -1:
                AppLogging.error("Somethign is wrong with clear")
                return

            invalid_entry = None
            invalid_entries = invalid_domain.entry_objects.all()
            if invalid_entries.exists() > 0:
                invalid_entry = invalid_entries[0]

            valid_domain_name = invalid_domain_name[:wh]
            link_with_https = "https://" + valid_domain_name

            b = EntryDataBuilder(link=link_with_https)
            if not b.result:
                AppLogging.error("Could not build the entry")

            if b.result == invalid_entry:
                # unattach
                invalid_entry.domain = None

                invalid_domain.delete()

            elif b.result != invalid_entry:
                w = EntryWrapper(invalid_entry)
                w.move_entry(b.result)

                # should also remove incorrect entry
                invalid_domain.delete()

    def cleanup_remove_entries(self, limit_s=0):
        if not self.cleanup_remove_entries_old_entries():
            return False

        if not self.cleanup_remove_entries_stale_entries():
            return False

        return True

    def cleanup_remove_entries_old_entries(self, limit_s=0):
        BATCH_SIZE = 1000

        sources = SourceDataController.objects.all()
        for source in sources:
            AppLogging.debug("Removing for source:{}".format(source.title))
            entries = self.get_source_old_entries_to_remove(source)

            if entries:
                for entry in entries:
                    AppLogging.debug("Removing source entry:{}".format(entry.link))
                # while entries.exists():
                #    entries[:BATCH_SIZE].delete()

        AppLogging.debug("Removing general entries")

        entries = self.get_general_old_entries_to_remove()
        if entries:
            for entry in entries:
                if entry.is_removable():
                    # AppLogging.debug("Removing general entry:{}".format(entry.link))
                    entry.delete()

        AppLogging.debug("Removing stale entries")

        return True

    def cleanup_remove_entries_stale_entries(self, limit_s=0):
        BATCH_SIZE = 1000
        sources = SourceDataController.objects.all()
        for source in sources:
            AppLogging.debug("Removing for source:{}".format(source.title))
            entries = self.get_source_stale_entries_to_remove(source)

            if entries:
                for entry in entries:
                    AppLogging.debug("Removing source entry:{}".format(entry.link))
                # while entries.exists():
                #    entries[:BATCH_SIZE].delete()

        AppLogging.debug("Removing general entries")

        entries = self.get_general_stale_entries_to_remove()
        if entries:
            for entry in entries:
                if entry.is_removable():
                    # AppLogging.debug("Removing general entry:{}".format(entry.link))
                    entry.delete()

        AppLogging.debug("Removing stale entries")

        return True

    def clean_archive(self):
        BATCH_SIZE = 1000

        config = Configuration.get_object().config_entry
        if config.days_to_move_to_archive == 0:
            entries = ArchiveLinkDataController.objects.all()
            entries.delete()
            # while entries.exists():
            #    entries[:BATCH_SIZE].delete()

        return True

    def get_source_old_entries_to_remove(self, source):
        """
        If links are old and should be removed
        """
        if not source.is_removable():
            return

        stale_conditions = self.get_old_conditions(source.get_days_to_remove())
        if not stale_conditions:
            return

        condition_source = Q(source=source) & stale_conditions

        return self.filter_objects(condition_source)

    def get_general_old_entries_to_remove(self):
        """
        If links are old and should be removed
        """
        stale_conditions = self.get_old_conditions()

        if not stale_conditions:
            return

        return self.filter_objects(stale_conditions)

    def get_source_stale_entries_to_remove(self, source):
        """
        If links are dead and should be removed
        """
        if not source.is_removable():
            return

        stale_conditions = self.get_stale_conditions(source.get_days_to_remove())
        if not stale_conditions:
            return

        condition_source = Q(source=source) & stale_conditions

        return self.filter_objects(condition_source)

    def get_general_stale_entries_to_remove(self):
        """
        If links are dead and should be removed
        """
        stale_conditions = self.get_stale_conditions()

        if not stale_conditions:
            return

        return self.filter_objects(stale_conditions)

    def get_stale_status_condition(self):
        return self.get_stale_status_condition_raw() & ~Q(manual_status_code=200)

    def get_stale_status_condition_raw(self):
        status_conditions_ok = Q(status_code=403) | Q(status_code=0)
        status_conditions_ok |= Q(status_code__gte=200) & Q(status_code__lte=300)

        return Q(~status_conditions_ok)

    def get_stale_conditions(self, days=None):
        config = Configuration.get_object().config_entry

        config_days = config.days_to_remove_stale_entries

        if days:
            if config_days != 0 and days == 0:
                days = config_days
            if config_days != 0 and config_days < days:
                days = config_days
        else:
            days = config_days

        if days == 0:
            return

        not_permanent_condition = Q(bookmarked=False, permanent=False)
        status_conditions_nok = self.get_stale_status_condition()

        page_rating_votes_exists = Q(page_rating_votes__gt=0)

        result_condition = (
            not_permanent_condition & status_conditions_nok & ~page_rating_votes_exists
        )

        if days != 0:
            days_before = DateUtils.get_days_before_dt(days)
            date_condition = Q(date_dead_since__lt=days_before)
            result_condition &= date_condition
        else:
            return None

        return result_condition

    def get_old_conditions(self, days=None):
        config = Configuration.get_object().config_entry

        config_days = config.days_to_remove_links

        if days:
            if config_days != 0 and days == 0:
                days = config_days
            if config_days != 0 and config_days < days:
                days = config_days
        else:
            days = config_days

        if days == 0:
            return

        not_permanent_condition = Q(bookmarked=False, permanent=False)
        page_rating_votes_exists = Q(page_rating_votes__gt=0)

        result_condition = not_permanent_condition & ~page_rating_votes_exists

        if days != 0:
            days_before = DateUtils.get_days_before_dt(days)
            date_condition = Q(date_created__lt=days_before) | Q(
                date_published__lt=days_before
            )
            result_condition &= date_condition
        else:
            return None

        return result_condition

    def get_stale_entries(self):
        """
        We only update current database, not archive
        """
        config = Configuration.get_object().config_entry
        days = config.days_to_remove_stale_entries
        if days == 0:
            return

        condition = self.get_stale_conditions()

        return self.filter_objects(condition)

    def filter_objects(self, input_conditions):
        if not self.archive_cleanup:
            return LinkDataController.objects.filter(input_conditions)
        else:
            return ArchiveLinkDataController.objects.filter(input_conditions)

    def move_old_links_to_archive(self):
        """
        TODO Refactor IT? I think we should operate on 'chunks' rather than entry-entry
        """
        entries = self.get_links_to_move_to_archive()
        # no more entries to process, cleaned up everything
        if not entries:
            return True

        AppLogging.debug("Moving link to archive")

        for entry in entries:
            EntryWrapper(entry=entry).move_to_archive()

        AppLogging.debug("Moving link to archive DONE")

        return True

    def get_links_to_move_to_archive(self):
        day_to_move = Configuration.get_object().get_entry_move_to_archive_date()

        if not day_to_move:
            return

        entries = LinkDataController.objects.filter(
            bookmarked=False, permanent=False, date_published__lt=day_to_move
        ).order_by("date_published")

        if not entries.exists():
            return

        return entries

    def move_existing_http_to_https(self):
        """
        Moves all duplicate links matching criteria
        """
        http_entries = LinkDataController.objects.filter(link__icontains="http://")
        if http_entries.exists():
            for http_entry in http_entries:
                https_url = http_entry.get_https_url()
                https_entries = LinkDataController.objects.filter(link=https_url)
                if https_entries.exists():
                    w = EntryWrapper(entry=http_entry)
                    w.move_entry(https_entries[0])

        return True

    def move_existing_www_to_nonwww(self):
        """
        Moves all duplicate links matching criteria
        """
        www_entries = LinkDataController.objects.filter(link__icontains="https://www.")
        if www_entries.exists():
            for www_entry in www_entries:
                nonwww_url = www_entry.link.replace("https://www.", "https://")
                nonwww_entries = LinkDataController.objects.filter(link=nonwww_url)
                if nonwww_entries.exists():
                    w = EntryWrapper(entry=www_entry)
                    w.move_entry(nonwww_entries[0])

        www_entries = LinkDataController.objects.filter(link__icontains="http://www.")
        if www_entries.exists():
            for www_entry in www_entries:
                nonwww_url = www_entry.link.replace("http://www.", "http://")
                nonwww_entries = LinkDataController.objects.filter(link=nonwww_url)
                if nonwww_entries.exists():
                    w = EntryWrapper(entry=www_entry)
                    w.move_entry(nonwww_entries[0])

        return True

    def is_time_exceeded(self):
        passed_seconds = time.time() - self.start_processing_time
        if passed_seconds >= self.limit_s:
            LinkDatabase.info("Task exeeded time:{}".format(passed_seconds))
            return True

        return False


class EntryCleanup(object):
    def __init__(self, entry):
        self.entry = entry

    def is_delete_time(self):
        if self.entry.is_permanent():
            """
            Cannot remove bookmarks, or permanent entries
            """
            return False

        if self.is_delete_by_config():
            return True

        if self.is_stale_and_dead_permanently():
            return True

        return False

    def is_delete_by_config(self):
        day_to_remove = Configuration.get_object().get_entry_remove_date()
        if not day_to_remove:
            return False

        return self.entry.date_published < day_to_remove

    def is_stale_and_dead_permanently(self):
        conf = Configuration.get_object().config_entry

        remove_days = conf.days_to_remove_stale_entries
        if remove_days == 0:
            """
            If remove_days is 0, then we do not remove any dead files
            """
            return False

        if (
            self.entry.is_dead()
            and self.entry.date_dead_since
            < DateUtils.get_datetime_now_utc() - timedelta(days=remove_days)
        ):
            return True

        return False


class EntryScanner(object):
    def __init__(self, url=None, entry=None, contents=None):
        if url:
            self.url = url
        if entry:
            self.url = entry.link

        self.contents = contents
        self.entry = entry

    def run(self):
        c = Configuration.get_object()
        config = c.config_entry
        if not config.auto_scan_new_entries:
            return

        if self.entry:
            if self.entry.page_rating < 0:
                return

        parser = ContentLinkParser(self.url, self.contents)

        contents_links = []
        if config.accept_domain_links:
            contents_links.extend(parser.get_domains())
        if config.accept_non_domain_links:
            contents_links.extend(parser.get_links())

        for link in contents_links:
            w = EntryWrapper(link=link)
            if not w.get():
                BackgroundJobController.link_add(link)


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

    def update_entry(self, all_properties):
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
            if "date_published" in properties and properties["date_published"]:
                if not entry.date_published:
                    entry.date_published = properties["date_published"]
                elif properties["date_published"] < entry.date_published:
                    entry.date_published = properties["date_published"]

        entry.date_update_last = DateUtils.get_datetime_now_utc()

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

        c = Configuration.get_object()
        config = c.config_entry

        if config.keep_social_data:
            BackgroundJobController.link_download_social_data(entry)

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

        EntryRules.check_all(self.entry)

        try:
            self.entry.refresh_from_db()
        except Exception as E:
            return

        w = EntryWrapper(entry=self.entry)
        w.evaluate()

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

        if not w.entry:
            return

        entry = w.entry

        url = EntryUrlInterface(entry.link, browser=self.browser)
        props = url.get_props()

        if url.is_server_error():
            raise IOError(f"{self.link}: Crawling server error")

        handler = UrlHandlerEx(url=entry.link)
        if handler.is_blocked():
            if entry.is_removable():
                entry.delete()
                return

        entry_changed = self.is_entry_changed(url.all_properties)

        config = Configuration.get_object().config_entry
        if config.auto_scan_updated_entries:
            BackgroundJobController.link_scan(entry.link)

        self.update_entry(url.all_properties)

        # we may not support update for some types. PDFs, other resources on the web
        if props and len(props) > 0:
            if "title" in props and props["title"] is not None:
                if not entry.title:
                    entry.title = props["title"]

            if "description" in props and props["description"] is not None:
                if not entry.description:
                    entry.description = props["description"]

            if "thumbnail" in props and props["thumbnail"] is not None:
                # always update
                entry.thumbnail = props["thumbnail"]

            if "language" in props and props["language"] is not None:
                if not entry.language:
                    entry.language = props["language"]

            if "date_published" in props and props["date_published"] is not None:
                if not entry.date_published:
                    entry.date_published = props["date_published"]

        if entry.date_dead_since:
            entry.date_dead_since = None

        self.update_calculated_vote()

        if not url.is_valid():
            self.handle_invalid_response(url)
            return

        if props and len(props) > 0:
            self.check_for_sources(entry, url)
            BackgroundJobController.link_scan(entry=entry)

            if entry_changed:
                self.add_links_from_url(entry, url)

            self.store_thumbnail(entry)

        entry.save()

    def reset_data(self):
        from ..pluginurl import EntryUrlInterface
        from ..pluginurl import UrlHandlerEx

        if not self.entry:
            return

        EntryRules.check_all(self.entry)

        try:
            self.entry.refresh_from_db()
        except Exception as E:
            return

        w = EntryWrapper(entry=self.entry)
        w.evaluate()

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

        if not w.entry:
            return

        entry = w.entry

        url = EntryUrlInterface(entry.link, browser=self.browser)
        props = url.get_props()
        if url.is_server_error():
            raise IOError(f"{self.link}: Crawling server error")

        handler = UrlHandlerEx(url=entry.link)
        if handler.is_blocked():
            link = entry.link
            if entry.is_removable():
                AppLogging.warning(f"Url:{link} Removing link. Blocked by a rule.")
                entry.delete()
                return

        config = Configuration.get_object().config_entry
        if config.auto_scan_updated_entries:
            BackgroundJobController.link_scan(entry.link)

        entry_changed = self.is_entry_changed(url.all_properties)

        self.update_entry(url.all_properties)

        # we may not support update for some types. PDFs, other resources on the web
        if props and len(props) > 0:
            if "title" in props and props["title"] is not None:
                entry.title = props["title"]

            if "description" in props and props["description"] is not None:
                entry.description = props["description"]

            if "thumbnail" in props and props["thumbnail"] is not None:
                entry.thumbnail = props["thumbnail"]

            if "language" in props and props["language"] is not None:
                entry.language = props["language"]

            if "date_published" in props and props["date_published"] is not None:
                if not entry.date_published:
                    entry.date_published = props["date_published"]

        if entry.date_dead_since is not None:
            entry.date_dead_since = None

        self.update_calculated_vote()

        if not url.is_valid():
            self.handle_invalid_response(url)
            return

        if props and len(props) > 0:
            if entry_changed:
                self.add_links_from_url(entry, url)

            self.check_for_sources(entry, url)
            BackgroundJobController.link_scan(entry=entry)
            self.store_thumbnail(entry)

    def store_thumbnail(self, entry):
        if entry.page_rating_votes > 0:  # TODO should that be configurable?
            from .modelfiles import ModelFilesBuilder

            c = Configuration.get_object()
            config = c.config_entry
            if config.auto_store_thumbnails:
                ModelFilesBuilder().build(file_name=entry.thumbnail)

    def add_links_from_url(self, entry, url_interface):
        properties = url_interface.all_properties

        if not properties:
            return

        server = RemoteServer("https://")
        contents = server.read_properties_section("Contents", properties)

        scanner = EntryScanner(url=entry.link, entry=entry, contents=contents)
        scanner.run()

    def reset_local_data(self):
        self.update_calculated_vote()

    def check_for_sources(self, entry, url_interface):
        conf = Configuration.get_object().config_entry

        if not conf.auto_create_sources:
            return

        url_handler = url_interface.h

        if not url_handler:
            return

        if not url_handler.p:
            return

        if url_handler.is_html():
            rss_urls = url_handler.p.get_rss_urls()

            for rss_url in rss_urls:
                SourceDataBuilder(link=rss_url).build_from_link()

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

    def handle_invalid_response(self, url_entry_interface):
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

        if url_entry_interface.all_properties:
            server = RemoteServer("")
            response = server.read_properties_section(
                "Response", url_entry_interface.all_properties
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


class EntryWrapper(object):
    """
    Wrapper for entry. Entries can reside in many places (operation table, archive table).
    This is unified API for them.

    Provides API to make links more uniform (http vs https)
    """

    def __init__(self, link=None, date=None, entry=None, user=None, strict_ids=False):
        """
        if strict_ids is true, then we use link_data "ids"
        """
        self.date = date
        self.entry = entry
        self.user = user
        self.strict_ids = strict_ids

        self.link = None
        if self.entry:
            self.link = self.entry.link
        if link:
            self.link = link

        if date is None:
            if self.entry:
                self.date = self.entry.date_published

    def get(self):
        """
        returns object from any relevant table: operation, archive
        """
        ob = self.get_internal()
        self.entry = ob
        return ob

    def get_internal(self):
        config = Configuration.get_object().config_entry
        if config.days_to_move_to_archive == 0:
            return self.get_from_db(LinkDataController.objects)

        if not self.link:
            return

        if self.date:
            is_archive = self.is_archive()

            if not is_archive:
                obj = self.get_from_db(LinkDataController.objects)
                if obj:
                    return obj
            else:
                obj = self.get_from_db(ArchiveLinkDataController.objects)
                if obj:
                    return obj

        else:
            obj = self.get_from_db(LinkDataController.objects)
            if obj:
                return obj

            obj = self.get_from_db(ArchiveLinkDataController.objects)
            if obj:
                return obj

    def get_from_db(self, objects):
        if self.link.startswith("http"):
            p = UrlLocation(self.link)

            """
            If there are links with www. at front, and without it, return the one without it
            """
            if p.get_domain_only().startswith("www."):
                link_url = p.get_protocol_url("https")
                link_url = link_url.replace("www.", "")
                entry_objs = objects.filter(link=link_url)

                if entry_objs.exists() and not entry_objs[0].is_dead():
                    return entry_objs[0]

                link_url = p.get_protocol_url("http")
                link_url = link_url.replace("www.", "")
                entry_objs = objects.filter(link=link_url)

                if entry_objs.exists() and not entry_objs[0].is_dead():
                    return entry_objs[0]

            link_https = p.get_protocol_url("https")
            https_objs = objects.filter(link=link_https)

            if https_objs.exists() and not https_objs[0].is_dead():
                return https_objs[0]

            link_http = p.get_protocol_url("http")
            http_objs = objects.filter(link=link_http)

            if http_objs.exists() and not http_objs[0].is_dead():
                return http_objs[0]

            """
            If both are dead - return https
            """

            if https_objs.exists():
                return https_objs[0]
            if http_objs.exists():
                return http_objs[0]

        objs = objects.filter(link=self.link)
        if objs.exists():
            return objs[0]

    def create(self, link_data):
        if "date_published" in link_data:
            self.date = link_data["date_published"]
        else:
            self.date = None

        is_archive = False
        if self.date:
            is_archive = self.is_archive()

        if "bookmarked" in link_data and link_data["bookmarked"]:
            is_archive = False
        if "permanent" in link_data and link_data["permanent"]:
            is_archive = False

        if (
            "language" in link_data
            and link_data["language"]
            and len(link_data["language"]) > 9
        ):
            AppLogging.error(
                "Language setting too long for:{} {}".format(
                    link_data["link"], link_data["language"]
                )
            )
            link_data["language"] = None

        title_length = LinkDataController.get_field_length("title")
        description_length = LinkDataController.get_field_length("description")

        if (
            "title" in link_data
            and link_data["title"]
            and len(link_data["title"]) > title_length - 1
        ):
            link_data["title"] = link_data["title"][: title_length - 1]
        if (
            "description" in link_data
            and link_data["description"]
            and len(link_data["description"]) > description_length - 1
        ):
            link_data["description"] = link_data["description"][
                : description_length - 1
            ]

        if not self.strict_ids and "id" in link_data:
            del link_data["id"]

        if self.user:
            link_data["user"] = self.user

        if not is_archive or self.date is None:
            if self.strict_ids and "id" in link_data:
                objs = LinkDataController.objects.filter(id=link_data["id"])
                if objs.exists():
                    return

            try:
                ob = LinkDataController.objects.create(**link_data)
            except Exception as E:
                AppLogging.exc(E, "Cannot create link {}".format(link_data))
                raise

        elif is_archive:
            if self.strict_ids and "id" in link_data:
                objs = ArchiveLinkDataController.objects.filter(id=link_data["id"])
                if objs.exists():
                    return

            try:
                ob = ArchiveLinkDataController.objects.create(**link_data)
            except Exception as E:
                AppLogging.exc(E, "Cannot create archive link {}".format(link_data))
                raise

        if ob:
            u = EntryUpdater(ob)
            u.reset_local_data()

        return ob

    def move_to_archive(self):
        entry_obj = self.entry
        link = entry_obj.link

        objs = ArchiveLinkDataController.objects.filter(link=entry_obj.link)

        if not objs.exists():
            themap = entry_obj.get_map(stringify=False)
            try:
                if hasattr(entry_obj, "source"):
                    if entry_obj.source:
                        themap["source"] = entry_obj.source
            except Exception as E:
                AppLogging.exc(E)

            try:
                if hasattr(entry_obj, "domain"):
                    if entry_obj.domain:
                        themap["domain"] = entry_obj.domain
            except Exception as E:
                AppLogging.exc(E)

            if "id" in themap:
                del themap["id"]

            archive_obj = ArchiveLinkDataController.objects.create(**themap)
            entry_obj.delete()
            return archive_obj
        else:
            entry_obj.delete()

    def move_from_archive(self):
        archive_obj = self.entry
        link = archive_obj.link

        objs = LinkDataController.objects.filter(link=archive_obj.link)
        if not objs.exists():
            themap = archive_obj.get_map(stringify=False)
            try:
                if hasattr(archive_obj, "source"):
                    if archive_obj.source:
                        themap["source"] = archive_obj.source
            except Exception as E:
                AppLogging.exc(E)
            try:
                if hasattr(archive_obj, "domain"):
                    if archive_obj.domain:
                        themap["domain"] = archive_obj.domain
            except Exception as E:
                AppLogging.exc(E)
            new_obj = LinkDataController.objects.create(**themap)
            archive_obj.delete()
            return new_obj
        else:
            archive_obj.delete()

    def make_bookmarked(self, request):
        """
        TODO move this API to UserBookmarks
        """
        entry = self.entry

        if entry.is_archive_entry():
            entry = self.move_from_archive()
            if not entry:
                AppLogging.error("Coult not move from archive")
                return

        if UserBookmarks.add(request.user, entry):
            entry.make_bookmarked()

        return entry

    def make_not_bookmarked(self, request):
        entry = self.entry

        UserBookmarks.remove(request.user, entry)

        if not UserBookmarks.is_bookmarked(entry):
            entry.make_not_bookmarked()
            self.evaluate()

        return entry

    def evaluate(self):
        """
        TODO rename to update()

        Checks:
         - if entry should be removed due to config accept_domain_links
         - updates permanent
         - if entry should be moved to archive
        """
        config = Configuration.get_object().config_entry

        entry = self.entry
        if not entry:
            return

        p = UrlLocation(entry.link)
        is_domain = p.is_domain()

        if not entry.should_entry_be_permanent():
            entry.permanent = False
        else:
            entry.permanent = True
        entry.save()

        if is_domain and not config.accept_domain_links:
            if entry.is_removable():
                entry.delete()
                self.entry = None
                return

        if not is_domain and not config.accept_non_domain_links:
            if entry.is_removable():
                entry.delete()
                self.entry = None
                return

        if entry.is_remove_time():
            if entry.is_removable():
                entry.delete()
                self.entry = None
                return

        if not entry.is_permanent() and entry.is_archive_time():
            return self.move_to_archive()

    def move_entry(self, destination_entry):
        """
        Moves entry to destination entry. Both objects need to exist.

        All properties are moved from source entry to destination entry.
        Source entry is destroyed
        """
        if self.entry is None:
            return

        if destination_entry.is_dead():
            return None

        from ..models import (
            UserTags,
            UserVotes,
            UserComments,
            UserBookmarks,
            UserEntryVisitHistory,
            UserEntryTransitionHistory,
        )

        source_entry = self.entry

        UserTags.move_entry(source_entry, destination_entry)
        UserVotes.move_entry(source_entry, destination_entry)
        UserComments.move_entry(source_entry, destination_entry)
        UserBookmarks.move_entry(source_entry, destination_entry)
        UserEntryVisitHistory.move_entry(source_entry, destination_entry)
        UserEntryTransitionHistory.move_entry(source_entry, destination_entry)

        source_entry.delete()
        self.entry = destination_entry

        u = EntryUpdater(self.entry)
        u.reset_local_data()

        return self.entry

    def move_entry_to_url(self, destination_url):
        """
        Moves entry to destination url.
        """
        destination_entries = LinkDataController.objects.filter(link=destination_url)

        if destination_entries.exists():
            return self.move_entry(destination_entries[0])
        else:
            self.entry.link = destination_url
            self.entry.save()

            return self.entry

    def is_archive(self):
        is_archive = BaseLinkDataController.is_archive_by_date(self.date)

        return is_archive

    def is_current_entry_perfect(self):
        from ..pluginurl import UrlHandlerEx, EntryUrlInterface

        entry = self.entry

        if not entry:
            return False

        if entry.is_https():
            if entry.link.startswith("https://www"):
                return False

            ping_status = UrlHandlerEx.ping(entry.link)

            return ping_status

    def check_https_http_availability(self):
        """
        We verify if http site also has properties. Sometime non-www pages return 200 status, but are blank
        TODO we do not want to fetch url interface each function like that

        @returns new object, or None object has not been changed
        """
        from ..pluginurl import UrlHandlerEx, EntryUrlInterface

        if not self.entry:
            return

        self.check_https_http_availability_entries()

        entry = self.entry

        c = Configuration.get_object().config_entry
        if not c.prefer_https_links:
            return

        if entry.is_https():
            http_url = entry.get_http_url()

            ping_status = UrlHandlerEx.ping(entry.link)

            if not ping_status:
                url = EntryUrlInterface(http_url)
                props = url.get_props()

                if url.is_valid() and props:
                    return EntryWrapper(entry=entry).move_entry_to_url(http_url)

            return self.entry

        if entry.is_http():
            https_url = entry.get_https_url()

            url = EntryUrlInterface(https_url)
            props = url.get_props()

            if url.is_valid() and props:
                return EntryWrapper(entry=entry).move_entry_to_url(https_url)

        return self.entry

    def check_www_nonww_availability(self):
        """
        We verify if non-www site also has properties. Sometime non-www pages return 200 status, but are blank
        TODO we do not want to fetch url interface each function like that

        @returns new object, or None if object has not been changed
        """
        from ..pluginurl import EntryUrlInterface

        if not self.entry:
            return

        self.check_www_nonww_availability_entries()

        c = Configuration.get_object().config_entry

        if not c.prefer_non_www_links:
            return

        entry = self.entry
        p = UrlLocation(entry.link)
        domain_only = p.get_domain_only()
        if not domain_only.startswith("www."):
            return self.entry

        destination_link = entry.link.replace("www.", "")

        url = EntryUrlInterface(destination_link)
        props = url.get_props()
        if url.is_valid() and props:
            return self.move_entry_to_url(destination_link)

        return self.entry

    def check_https_http_availability_entries(self):
        """
        Removes http<>https duplicates, if we have http and https pages select https to be present
        """
        entry = self.entry

        if entry.is_https():
            http_url = entry.get_http_url()

            http_entries = LinkDataController.objects.filter(link=http_url)
            if http_entries.exists():
                w = EntryWrapper(entry=http_entries[0])
                w.move_entry(entry)

        if entry.is_http():
            https_url = entry.get_https_url()

            # if we have both, destroy http entry
            https_entries = LinkDataController.objects.filter(link=https_url)
            if https_entries.exists():
                self.move_entry(https_entries[0])

        return self.entry

    def check_www_nonww_availability_entries(self):
        """
        Removes non-www and www pages duplicates.
        """
        entry = self.entry

        p = UrlLocation(entry.link)

        url_parts = p.parse_url()
        domain_only = url_parts[2].lower()

        if domain_only.startswith("www."):
            link_with_www = entry.link
            link_without_www = entry.link.replace("www.", "")
        else:
            # TODO should there be API for that?
            link_without_www = entry.link
            joined = "/".join(url_parts[1:])
            link_with_www = url_parts[0] + "www." + joined

        if domain_only.startswith("www."):
            entries = LinkDataController.objects.filter(link=link_without_www)
            if entries.exists():
                self.move_entry(entries[0])
        else:
            entries = LinkDataController.objects.filter(link=link_with_www)
            if entries.exists():
                self.move_entry(self.entry)


class EntryCrawler(object):
    def __init__(self, link, contents, source=None):
        self.link = link
        self.contents = contents
        self.source = source

    def get_links(self):
        """
        Adds links from description of that link.
        Store link as-is.
        """
        config = Configuration.get_object().config_entry

        if config.auto_crawl_sources:
            links = self.get_crawl_links()

            for link in links:
                BackgroundJobController.link_add(
                    url=link, source=self.source
                )

    def get_crawl_links(self):
        links = set()

        parser = ContentLinkParser(
            self.link, self.contents
        )

        config = Configuration.get_object().config_entry

        if config.accept_non_domain_links:
            links = set(parser.get_links())

        if config.accept_domain_links:
            links = set(parser.get_domains())

            p = UrlLocation(self.link)
            domain = p.get_domain()
            if domain and domain != self.link:
                links.add(domain)

        links -= {self.link}

        return links


class EntryDataBuilder(object):
    """
    - sometimes we want to call this object directly, sometimes it should be redirected to "add link background job"
    - we do not change data in here, we do not correct, we just follow it (I think that is what should be)
    - all subservent entries are added by background controller, handled in a separate task
    - we cannot spend too much time in builder from any context. This code should be possibly fast
    - if there is a possibility to not search it, we do not do it
    """

    def __init__(
        self,
        link=None,
        link_data=None,
        source_is_auto=True,
        user=None,
        allow_recursion=True,
        ignore_errors=False,
        strict_ids=False,
        browser=None,
    ):
        self.link = link
        self.link_data = link_data
        self.source_is_auto = source_is_auto
        self.allow_recursion = allow_recursion
        self.user = user
        self.strict_ids = strict_ids
        self.browser = browser
        self.errors = []

        self.ignore_errors = ignore_errors
        c = Configuration.get_object().config_entry
        if c.accept_dead_links:
            self.ignore_errors = True

        self.result = None

        if self.link:
            self.build_from_link()

        if self.link_data:
            self.build_from_props(ignore_errors=self.ignore_errors)

    def build(
        self,
        link=None,
        link_data=None,
        source_is_auto=True,
        allow_recursion=True,
        ignore_errors=False,
        strict_ids=False,
        browser=None,
    ):
        self.link = link
        self.link_data = link_data
        self.strict_ids = strict_ids
        self.source_is_auto = source_is_auto
        self.browser = browser

        if self.link:
            return self.build_from_link()

        if self.link_data:
            return self.build_from_props(ignore_errors=self.ignore_errors)

    def build_simple(self, link=None, user=None, source_is_auto=True, browser=None):
        if link:
            self.link = link
        self.browser = browser

        wrapper = EntryWrapper(link=self.link)
        entry = wrapper.get()
        if entry:
            self.result = entry
            return entry

        self.user = user
        self.source_is_auto = source_is_auto

        link_data = {}
        link_data["link"] = self.link
        link_data["user"] = self.user

        entry = wrapper.create(link_data)

        if entry:
            config = Configuration.get_object().config_entry
            if config.enable_domain_support:
                DomainsController.add(entry.link)

            BackgroundJobController.entry_update_data(entry=entry, browser=self.browser)
            BackgroundJobController.link_scan(entry=entry, browser=browser)
            BackgroundJobController.link_save(entry.link)

        return entry

    def build_from_link(self, link=None, ignore_errors=False):
        from ..pluginurl import UrlHandlerEx

        if link:
            self.link = link

        """
        TODO extract this to a separate class?
        """
        self.ignore_errors = ignore_errors
        self.link = UrlHandlerEx.get_cleaned_link(self.link)
        if not self.link:
            return

        p = UrlLocation(self.link)
        if p.is_link_service():
            return self.build_from_link_service()
        else:
            return self.build_from_normal_link()

    def build_from_link_service(self):
        from ..pluginurl import EntryUrlInterface

        url = EntryUrlInterface(self.link, ignore_errors=self.ignore_errors)
        link_data = url.get_props()

        if url.is_server_error():
            raise IOError(f"{self.link}: Crawling server error")

        if self.source_is_auto and not url.is_valid():
            self.errors.append("Url:{}. Url is not valid".format(self.link))
            AppLogging.debug(
                "Url:{} Could not obtain properties for {}".format(self.link, self.link)
            )
            return

        if not link_data:
            if Configuration.get_object().config_entry.debug_mode:
                self.errors.append(
                    "Url:{}. Could not obtain link service properties".format(self.link)
                )
                AppLogging.debug(
                    'Could not obtain properties for:<a href="{}">{}</a>'.format(
                        self.get_absolute_url(), self.link
                    )
                )
            return

        self.link_data = link_data
        return self.build_from_props(ignore_errors=self.ignore_errors)

    def build_from_normal_link(self):
        from ..pluginurl import EntryUrlInterface

        """
        TODO move this to a other class OnlyLinkDataBuilder?
        """
        wrapper = EntryWrapper(link=self.link)
        obj = wrapper.get()
        if obj:
            self.result = obj
            return obj

        if not self.link_data:
            self.link_data = {}

        self.link_data["link"] = self.link

        # we do not want to obtain properties for non-domain entries, if we capture only
        # domains
        if not self.is_enabled_to_store():
            self.errors.append("Url:{}. Not enabled to store".format(self.link))
            return

        rule = EntryRules.is_url_blocked(self.link_data["link"])
        if rule:
            self.errors.append(
                "Url:{}. Link was rejected because of a rule. {}".format(
                    self.link, rule
                )
            )
            return

        url = EntryUrlInterface(
            self.link, ignore_errors=self.ignore_errors, browser=self.browser
        )

        link_data = url.get_props()

        if url.is_server_error():
            raise IOError(f"{self.link}: Crawling server error")

        if url.is_blocked():
            self.errors.append("Url:{}. Url is blocked".format(self.link))
            AppLogging.debug(
                "Url:{} Could not obtain properties for {}".format(self.link, self.link)
            )
            return

        if self.source_is_auto and not url.is_valid():
            self.errors.append("Url:{}. Url is not valid".format(self.link))
            AppLogging.debug(
                "Url:{} Could not obtain properties for {}".format(self.link, self.link)
            )
            return

        if not link_data:
            if Configuration.get_object().config_entry.debug_mode:
                self.errors.append(
                    "Url:{}. Could not obtain properties".format(self.link)
                )
                AppLogging.debug(
                    "Url:{} Could not obtain properties for {}".format(
                        self.link, self.link
                    )
                )
            return

        self.merge_link_data(link_data)

        if self.link_data:
            return self.build_from_props_internal()
        else:
            if Configuration.get_object().config_entry.debug_mode:
                self.errors.append(
                    "Url:{}. Could not obtain properties for link.".format(self.link)
                )
                AppLogging.debug(
                    'Could not obtain properties for:<a href="{}">{}</a>'.format(
                        self.link, self.link
                    )
                )

    def merge_link_data(self, link_data):
        # TODO update missing keys - do not replace them
        new_link_data = None

        if self.link_data and link_data:
            new_link_data = {**self.link_data, **link_data}
        if self.link_data:
            new_link_data = self.link_data
        if link_data:
            new_link_data = link_data

        self.link_data = new_link_data
        return self.link_data

    def is_property_set(self, link_data, property_name):
        return (
            property_name in link_data
            and link_data[property_name] != None
            and len(link_data[property_name]) > 0
        )

    def is_link_data_valid_for_auto_add(self, link_data):
        from ..pluginurl import UrlHandlerEx

        if not self.is_property_set(link_data, "title"):
            return False

        if "status_code" in link_data and link_data["status_code"]:
            h = UrlHandlerEx(link_data["link"])
            if h.is_status_code_invalid(link_data["status_code"]):
                return False

        if "is_valid" in link_data and not link_data["is_valid"]:
            return False

        return True

    def build_from_props(self, ignore_errors=False):
        from ..pluginurl import UrlHandlerEx

        self.ignore_errors = ignore_errors

        url = self.link_data["link"]
        if not url:
            return

        obj = None

        self.link_data["link"] = UrlHandlerEx.get_cleaned_link(self.link_data["link"])
        self.link = self.link_data["link"]

        if self.is_too_old():
            return

        wrapper = EntryWrapper(link=self.link)
        entry = wrapper.get()
        if entry:
            self.result = entry
            return entry

        entry = self.build_from_props_internal()
        self.result = entry
        return entry

    def is_too_old(self):
        day_to_remove = Configuration.get_object().get_entry_remove_date()
        if not day_to_remove:
            return False

        if (
            self.source_is_auto
            and "date_published" in self.link_data
            and self.link_data["date_published"]
        ):
            if self.link_data["date_published"] < day_to_remove:
                return True

        return False

    def build_from_props_internal(self):
        entry = None

        # we obtain links from various places. We do not want technical links with no data, redirect, CDN or other
        if not self.is_link_data_valid_for_auto_add(self.link_data):
            self.errors.append(
                "Url:{}. Link is not valid for auto add".format(self.link)
            )
            return

        self.link_data = self.get_clean_link_data()
        rule = EntryRules.is_url_blocked(self.link_data["link"])
        if rule:
            self.errors.append(
                "Url:{}. Link was rejected because of a rule. {}".format(
                    self.link, rule
                )
            )
            return

        # TODO - what if there are many places and we do not want people to insert
        # bad stuff?
        if self.source_is_auto:
            if "title" not in self.link_data or not self.link_data["title"]:
                self.errors.append(
                    "Url:{}. Link was rejected not title.".format(self.link)
                )
                return

            if EntryRules.is_dict_blocked(self.link_data):
                self.errors.append(
                    "Url:{}. Link was rejected due contents rule - by checking properties.".format(
                        self.link
                    )
                )
                return

            if len(self.link_data["link"]) > LinkDataController.get_field_length(
                "link"
            ):
                self.errors.append("Url:{}. Link too long".format(self.link))
                return

        # if self.source_is_auto:
        #    self.link_data["link"] = self.link_data["link"].lower()

        c = Configuration.get_object().config_entry

        if self.is_enabled_to_store():
            date = None
            if "date_published" in self.link_data:
                date = self.link_data["date_published"]
            wrapper = EntryWrapper(link=self.link_data["link"], date=date)
            entry = wrapper.get()

            if entry:
                return entry

            self.link_data = self.check_and_set_source_object()
            self.link_data = self.set_domain_object()

            entry = self.add_entry_internal()

            # TODO if object just created
            if entry:
                c = Configuration.get_object().config_entry
                if c.new_entries_use_clean_data:
                    BackgroundJobController.entry_reset_data(entry)
                elif c.new_entries_merge_data:
                    BackgroundJobController.entry_update_data(entry)

                self.add_addition_link_data(entry)

        return entry

    def get_clean_link_data(self):
        props = self.link_data
        props = LinkDataController.get_clean_data(props)
        return props

    def is_domain_link_data(self):
        link_data = self.link_data
        p = UrlLocation(link_data["link"])
        return p.get_domain() == link_data["link"]

    def add_entry_internal(self):
        link_data = self.link_data

        new_link_data = dict(link_data)
        if "date_published" not in new_link_data:
            new_link_data["date_published"] = DateUtils.get_datetime_now_utc()
        if "date_update_last" not in new_link_data:
            new_link_data["date_update_last"] = DateUtils.get_datetime_now_utc()

        if (
            "page_rating" not in new_link_data
            or "page_rating" in new_link_data
            and new_link_data["page_rating"] == 0
        ):
            if "page_rating_contents" in new_link_data:
                new_link_data["page_rating"] = new_link_data["page_rating_contents"]

        if "age" not in new_link_data:
            age = EntryRules.get_age_for_dictionary(new_link_data)
            if age:
                new_link_data["age"] = age

        AppLogging.debug("Adding link: {}".format(new_link_data["link"]))

        wrapper = EntryWrapper(
            link=new_link_data["link"],
            date=new_link_data["date_published"],
            user=self.user,
            strict_ids=self.strict_ids,
        )

        entry = wrapper.create(new_link_data)

        if entry:
            BackgroundJobController.link_scan(entry=entry)

        return entry

    def set_domain_object(self):
        config = Configuration.get_object().config_entry

        if config.enable_domain_support:
            domain = DomainsController.add(self.link_data["link"])

            if domain:
                self.link_data["domain"] = domain
        return self.link_data

    def check_and_set_source_object(self):
        link_data = self.link_data

        if "source" not in link_data and "source_url" in link_data:
            source_obj = None
            sources = SourceDataController.objects.filter(url=link_data["source_url"])
            if sources.exists():
                source_obj = sources[0]

            link_data["source"] = source_obj

        return link_data

    def is_enabled_to_store(self):
        # manual entry is always enabled
        if not self.source_is_auto:
            return True

        config = Configuration.get_object().config_entry
        link = self.link_data["link"]

        p = UrlLocation(link)
        is_domain = p.is_domain()
        domain = p.get_domain_only()

        if not config.accept_non_domain_links:
            if is_domain and config.accept_domain_links:
                pass
            elif not is_domain and config.accept_domain_links:
                return False
            elif "bookmarked" in self.link_data and self.link_data["bookmarked"]:
                pass
            else:
                return False

        # we do not store link services, we can store only what is behind those links
        p = UrlLocation(link)
        if p.is_link_service():
            return False

        # heavier checks last
        if self.is_live_video():
            return False

        if not config.accept_ip_links:
            if self.is_ipv4(domain):
                return False

        return True

    def is_ipv4(self, string):
        try:
            ipaddress.IPv4Network(string)
            return True
        except ValueError:
            return False

    def is_live_video(self):
        link_data = self.link_data

        if "live" in link_data and link_data["live"]:
            return link_data["live"]

        return False

    def add_addition_link_data(self, entry):
        link_data = self.link_data

        self.add_sub_links(entry)
        # self.add_keywords(entry) # TODO
        # self.add_domain(entry) # TODO
        self.add_socialdata(entry)

        if entry:
            self.download_thumbnail(entry.thumbnail)

    def add_domain(self, entry):
        # TODO
        # url = UrlLocation(entry.link).get_domain()
        #    if "source" in self.link_data:
        #        BackgroundJobController.link_add(
        #            url=url, source=self.link_data["source"]
        #        )
        #    else:
        #        BackgroundJobController.link_add(url=url)
        pass

    def add_socialdata(self, entry):
        SocialData.get(entry)

    def download_thumbnail(self, thumbnail_path):
        if thumbnail_path:
            config = Configuration.get_object().config_entry
            if config.auto_store_thumbnails:
                BackgroundJobController.download_file(thumbnail_path)

    def add_sub_links(self, entry):
        """
        Adds links from description of that link.
        Store link as-is.
        """
        config = Configuration.get_object().config_entry

        link_data = self.link_data

        if config.auto_crawl_sources:
            link = link_data.get("link")
            source = link_data.get("source")

            description = link_data.get("description")

            crawler = EntryCrawler(link_data["link"], description, source)

            links = crawler.get_links()

            contents = link_data.get("contents")
            crawler = EntryCrawler(link_data["link"], contents, source)

            links.update(crawler.get_links())

            for link in links:
                BackgroundJobController.link_add(
                    url=link, source=source
                )

        if config.auto_scan_new_entries:
            BackgroundJobController.link_scan(link_data["link"])

    def add_keywords(self, entry):
        config = Configuration.get_object().config_entry

        if config.enable_keyword_support:
            if entry.title and entry.title != "":
                KeyWords.add_link_data(entry.title)

    def read_domains_from_bookmarks():
        objs = LinkDataController.objects.filter(bookmarked=True)
        for obj in objs:
            p = UrlLocation(obj.link)
            EntryDataBuilder(link=p.get_domain())


class EntriesCleanupAndUpdate(object):
    def cleanup(self, limit_s=0):
        start_processing_time = time.time()

        cleanup = EntriesCleanup(
            archive_cleanup=False, start_processing_time=start_processing_time
        )
        if not cleanup.cleanup(limit_s):
            return False

        cleanup = EntriesCleanup(
            archive_cleanup=True, start_processing_time=start_processing_time
        )
        if not cleanup.cleanup(limit_s):
            return False

        # indicate that all has been finished correctly
        return True
