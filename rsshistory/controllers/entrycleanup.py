from datetime import timedelta
import time

from django.db import models
from django.db.models import Q, F

from utils.dateutils import DateUtils

from ..models import (
    AppLogging,
    EntryRules,
)
from ..configuration import Configuration
from ..apps import LinkDatabase
from .entries import LinkDataController, ArchiveLinkDataController
from .entrywrapper import EntryWrapper
from .domains import DomainsController
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
