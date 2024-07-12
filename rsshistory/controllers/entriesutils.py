from datetime import timedelta
import traceback
import time
import ipaddress

from django.db import models
from django.urls import reverse
from django.db.models import Q, F

from ..models import (
    BaseLinkDataController,
    AppLogging,
    KeyWords,
    UserBookmarks,
    ModelFiles,
)
from ..configuration import Configuration
from ..webtools import RequestBuilder, HtmlPage, RssPage, ContentLinkParser, DomainAwarePage
from ..apps import LinkDatabase
from ..dateutils import DateUtils
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
            self.limit_s = 60*10 # 10 minutes
        else:
            self.limit_s = limit_s

    def cleanup(self, limit_s = 0):
        """
        We do not exit prematurely.

        Reason: if user has 200'000 links it make take a long time.
        During cleanup new links may become outdated.
        Cleanup may never end if we enter here for a few seconds only.
        Provide more queues, if you want such jobs to not clog queues.

        @return True if successful
        """
        if not self.cleanup_remove_entries():
            return False

        if not self.cleanup_invalid_page_ratings():
            return False

        config = Configuration.get_object().config_entry
        if config.prefer_https:
            if not self.move_existing_http_to_https():
                return False

        if config.prefer_non_www_sites:
            if not self.move_existing_www_to_nonwww():
                return False

        if not self.archive_cleanup:
            if not self.move_old_links_to_archive():
                return False

        # self.cleanup_entries_with_ports()

        # TODO it may take very long time, exceed time, and be correct, we should
        # return True then. Check if everything has been done, not only exceeded time

        #self.cleanup_permanent_flags()

        #if self.is_time_exceeded():
        #    return False

        return True

    def cleanup_entries_with_ports(self):
        """
        This will only fix domains
        """
        invalid_domains = DomainsController.objects.filter(domain__icontains = ":")
        for invalid_domain in invalid_domains:
            invalid_domain_name = invalid_domain.domain
            wh = invalid_domain_name.find(":")
            if wh == -1:
                AppLogging.error("Somethign is wrong with clear")
                return

            invalid_entry = None
            invalid_entries = invalid_domain.entry_objects.all()
            if invalid_entries.count() > 0:
                invalid_entry = invalid_entries[0]

            valid_domain_name = invalid_domain_name[:wh]
            link_with_https = "https://"+valid_domain_name

            b = EntryDataBuilder(link=link_with_https)
            if not b.result:
                AppLogging.error("Could not build the entry")

            if b.result == invalid_entry:
                # unattach
                invalid_entry.domain_obj = None

                invalid_domain.delete()

            elif b.result != invalid_entry:
                w = EntryWrapper(invalid_entry)
                w.move_entry(b.result)

                # should also remove incorrect entry
                invalid_domain.delete()

    def cleanup_remove_entries(self, limit_s = 0):
        sources = SourceDataController.objects.all()
        for source in sources:
            AppLogging.debug("Removing for source:{}".format(source.title))
            entries = self.get_source_entries(source)

            if entries:
                for entry in entries:
                    AppLogging.debug("Removing entry:{}".format(entry.link))
                entries.delete()

        entries = self.get_general_entries()
        if entries:
            for entry in entries:
                AppLogging.debug("Removing entry:{}".format(entry.link))
            entries.delete()

        if not self.archive_cleanup:
            entries = self.get_stale_entries()
            if entries:
                for entry in entries:
                    AppLogging.debug("Removing entry:{}".format(entry.link))
                entries.delete()

        return True

    def is_time_exceeded(self):
        passed_seconds = time.time() - self.start_processing_time
        if passed_seconds >= self.limit_s:
            LinkDatabase.info("Task exeeded time:{}".format(passed_seconds))
            return True

        return False

    def get_source_entries(self, source):
        """
        Choose shorter date - configured, or source limit
        """
        config = Configuration.get_object().config_entry
        config_days = config.days_to_remove_links

        if not source.is_removeable():
            return

        days = source.get_days_to_remove()

        if config_days != 0 and days == 0:
            days = config_days
        if config_days != 0 and config_days < days:
            days = config_days

        if days == 0:
            return

        days_before = DateUtils.get_days_before_dt(days)

        condition_source = Q(source=source.url) & Q(date_published__lt=days_before)
        if config.keep_permanent_items:
            condition_source &= Q(bookmarked=False, permanent=False)

        if not self.archive_cleanup:
            entries = LinkDataController.objects.filter(condition_source).order_by(
                "date_published"
            )

        else:
            entries = ArchiveLinkDataController.objects.filter(
                condition_source
            ).order_by("date_published")

        if entries and entries.exists():
            return entries

    def get_general_entries(self):
        config = Configuration.get_object().config_entry
        config_days = config.days_to_remove_links

        days = config_days
        if days == 0:
            return

        days_before = DateUtils.get_days_before_dt(days)

        condition = Q(date_published__lt=days_before)
        if config.keep_permanent_items:
            condition &= Q(bookmarked=False, permanent=False)

        if not self.archive_cleanup:
            entries = LinkDataController.objects.filter(condition)
        else:
            entries = ArchiveLinkDataController.objects.filter(condition)

        if entries.exists():
            return entries

    def get_stale_entries(self):
        """
        We only update current database, not archive
        """
        config = Configuration.get_object().config_entry
        days = config.days_to_remove_stale_entries
        if days == 0:
            return

        days_before = DateUtils.get_days_before_dt(days)

        condition = Q(date_published__lt=days_before)
        if config.keep_permanent_items:
            condition &= Q(bookmarked=False, permanent=False)

        entries = LinkDataController.objects.filter(condition)

        if entries.exists():
            return entries

    def cleanup_invalid_page_ratings(self):
        condition = Q(page_rating__gte=100)
        condition2 = Q(page_rating__gte=F("page_rating_contents")) & Q(
            page_rating_votes=0
        )
        if not self.archive_cleanup:
            entries = LinkDataController.objects.filter(condition | (condition2))

            for entry in entries:
                u = EntryUpdater(entry)
                u.reset_local_data()

        return True

    def move_old_links_to_archive(self):
        """
        TODO Refactor IT? I think we should operate on 'chunks' rather than entry-entry
        """
        entries = self.get_links_to_move_to_archive()
        # no more entries to process, cleaned up everything
        if not entries:
            return True

        for entry in entries:
            AppLogging.debug("Moving link to archive: {}".format(entry.link))
            EntryWrapper(entry=entry).move_to_archive()

        return True

    def get_links_to_move_to_archive(self):
        conf = Configuration.get_object().config_entry

        if conf.days_to_move_to_archive == 0:
            return

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)

        entries = LinkDataController.objects.filter(
            bookmarked=False, permanent=False, date_published__lt=days_before
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
                    w = EntryWrapper(entry = http_entry)
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
                    w = EntryWrapper(entry = www_entry)
                    w.move_entry(nonwww_entries[0])

        www_entries = LinkDataController.objects.filter(link__icontains="http://www.")
        if www_entries.exists():
            for www_entry in www_entries:
                nonwww_url = www_entry.link.replace("http://www.", "http://")
                nonwww_entries = LinkDataController.objects.filter(link=nonwww_url)
                if nonwww_entries.exists():
                    w = EntryWrapper(entry = www_entry)
                    w.move_entry(nonwww_entries[0])

        return True

    def cleanup_permanent_flags(self):
        """
        Permaments are:
         - if enable_domain_support & keep_domains
        This could be intensive
        """
        link_is_url = Q(source_obj__url = F('link'))
        domain_is_notnull = Q(domain_obj__isnull=False)
        is_permanent = Q(permanent = True)

        # domain is not null and link is url are valid scenarios

        entries = LinkDataController.objects.filter( ~(link_is_url | domain_is_notnull) & is_permanent)
        for entry in entries:
            entry.permanent = False
            entry.save()


class EntryCleanup(object):
    def __init__(self, entry):
        self.entry = entry

    def is_delete_time(self):
        if self.entry.is_permanent():
            """
            Cannot remove bookmarks, or permament entries
            """
            return False

        if self.is_delete_by_config():
            return True

        if self.is_stale_and_dead_permanently():
            return True

        return False

    def is_delete_by_config(self):
        conf = Configuration.get_object().config_entry
        if conf.days_to_remove_links == 0:
            return False

        day_to_remove = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_links
        )

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
        if not config.auto_scan_entries:
            return

        if self.entry:
            if self.entry.page_rating < 0:
                return

        parser = ContentLinkParser(self.url, self.contents)

        contents_links = []
        if config.accept_domains:
            contents_links = parser.get_domains()
        if config.accept_not_domain_entries:
            contents_links = parser.get_links()

        for link in contents_links:
            BackgroundJobController.link_add(link)


class EntryUpdater(object):
    def __init__(self, entry):
        self.entry = entry

    def is_entry_changed(self, url_handler):
        entry = self.entry

        response = url_handler.get_response()
        if not response:
            return True

        last_modified_date = response.get_last_modified()
        if last_modified_date:
            if not entry.date_last_modified:
                return True

            if last_modified_date > entry.date_last_modified:
                return True

            return False

        body_hash = url_handler.get_contents_body_hash()
        if body_hash:
            if not entry.body_hash:
                return True

            if entry.body_hash == body_hash:
                return False

            return True

        contents_hash = url_handler.get_contents_hash()
        if contents_hash:
            if not entry.contents_hash:
                return True

            if entry.contents_hash == contents_hash:
                return False

            return True

        return True

    def update_entry(self, url_handler):
        entry = self.entry

        response = url_handler.get_response()
        if response:
            entry.date_last_modified = response.get_last_modified()
            entry.status_code = response.get_status_code()
        entry.date_update_last = DateUtils.get_datetime_now_utc()

        entry.body_hash = url_handler.get_contents_body_hash()
        entry.contents_hash = url_handler.get_contents_hash()
        entry.page_rating_contents = url_handler.get_page_rating()

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

        entry.save()

    def update_data(self):
        from ..pluginurl import EntryUrlInterface

        """
        Fetches new information about page, and uses valid fields to set this object,
        but only if current field is not set

         - status code and page rating is update always
         - title and description could have been set manually, we do not want to change that
         - some other fields should be set only if present in props
        """

        w = EntryWrapper(entry=self.entry)
        w.evaluate()
        w.check_https_http_availability()
        w.check_www_nonww_availability()

        if not w.entry:
            return

        entry = w.entry

        url = EntryUrlInterface(entry.link)
        props = url.get_props()
        p = url.p

        if url.h:
            if url.h.is_blocked():
                entry.delete()
                return

        entry_changed = self.is_entry_changed(url.h)

        self.update_entry(url.h)

        if not url.is_valid():
            self.handle_invalid_response(url)
            return

        # we may not support update for some types. PDFs, other resources on the web
        if not props or len(props) == 0:
            return

        if entry.date_dead_since:
            entry.date_dead_since = None

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

        self.update_calculated_vote()
        # save is performed by the above

        self.check_for_sources(entry, url)

        if entry_changed:
            self.add_links_from_url(entry, url)

        self.store_thumbnail(entry)

    def reset_data(self):
        from ..pluginurl import EntryUrlInterface

        """
        Fetches new information about page, and uses valid fields to set this object.

         - status code and page rating is update always
         - new data are changed only if new data are present at all
        """
        w = EntryWrapper(entry=self.entry)
        w.evaluate()
        w.check_https_http_availability()
        w.check_www_nonww_availability()

        if not w.entry:
            return

        entry = w.entry

        url = EntryUrlInterface(entry.link)
        props = url.get_props()

        if url.h:
            if url.h.is_blocked():
                entry.delete()
                return

        entry_changed = self.is_entry_changed(url.h)

        self.update_entry(url.h)

        if not url.is_valid():
            self.handle_invalid_response(url)
            return

        # we may not support update for some types. PDFs, other resources on the web
        if not props or len(props) == 0:
            return

        if entry.date_dead_since:
            entry.date_dead_since = None

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

        self.update_calculated_vote()

        if entry_changed:
            self.add_links_from_url(entry, url)

        self.check_for_sources(entry, url)
        self.store_thumbnail(entry)

    def store_thumbnail(self, entry):
        if entry.page_rating_votes > 0: # TODO should that be configurable?
            from .modelfiles import ModelFilesBuilder

            c = Configuration.get_object()
            config = c.config_entry
            if config.auto_store_thumbnails:
                ModelFilesBuilder().build(file_name = entry.thumbnail)

    def add_links_from_url(self, entry, url_interface):
        url_handler = url_interface.h

        if not url_handler:
            return

        if not url_handler.p:
            return

        scanner = EntryScanner(
            url=url_handler.url, entry=entry, contents=url_handler.p.get_contents()
        )
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
                SourceDataBuilder(link=rss_url).add_from_link()

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

        visits = UserEntryVisitHistory.objects.filter(entry_object=self.entry)

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
            if tags.count() > 0:
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
            error_text = traceback.format_exc()

            AppLogging.error(
                'Cannot access link:<a href="{}">{}</a>\n{}'.format(
                    entry.get_absolute_url(), entry.link, error_text
                )
            )
            entry.date_dead_since = DateUtils.get_datetime_now_utc()
            entry.save()

        cleanup = EntryCleanup(entry)

        link = self.entry.link
        date = self.entry.date_dead_since

        if cleanup.is_delete_time():
            self.entry.delete()

            AppLogging.notify(
                "Removed entry <a href='{}'>{}</a>. It was dead since {}.".format(
                    link, link, date
                )
            )
            return

        entry.page_rating_contents = 0
        if url_entry_interface.h:
            entry.status_code = url_entry_interface.h.get_status_code()
        else:
            entry.status_code = BaseLinkDataController.STATUS_DEAD
        entry.save()


class EntriesUpdater(object):
    def get_entries_to_update(self):
        """
        @note
        Normal entries are checked with interval days_to_check_std_entries
        Dead entries are checked with interval days_to_check_stale_entries
        """
        c = Configuration.get_object()
        conf = c.config_entry

        if conf.days_to_check_std_entries == 0:
            return

        date_to_check_std = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_check_std_entries
        )
        date_to_check_stale = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_check_stale_entries
        )

        condition_days_to_check_std = Q(date_update_last__lt=date_to_check_std)
        condition_days_to_check_stale = Q(date_update_last__lt=date_to_check_stale)

        condition_not_dead = Q(date_dead_since__isnull=False)
        condition_dead = Q(date_dead_since__isnull=True)

        condition_update_null = Q(date_update_last__isnull=True)

        entries = LinkDataController.objects.filter(
             condition_update_null |
             (condition_not_dead & condition_days_to_check_std) |
             (condition_dead & condition_days_to_check_stale)
        ).order_by("date_update_last", "link")

        return entries


class EntryWrapper(object):
    """
    Wrapper for entry. Entries can reside in many places (operation table, archive table).
    This is unified API for them.

    Provides API to make links more uniform (http vs https)
    """

    def __init__(self, link=None, date=None, entry=None):
        self.date = date
        self.entry = entry

        if link is None:
            if self.entry:
                self.link = self.entry.link
        else:
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
        conf = Configuration.get_object().config_entry

        if self.link.startswith("http"):
            p = DomainAwarePage(self.link)

            """
            If there are links with www. at front, and without it, return the one without it
            """
            if p.get_domain_only().startswith("www."):
                link_url = p.get_protocol_url("https")
                link_url = link_url.replace("www.", "")
                entry_objs = objects.filter(link=link_url)

                if entry_objs.count() > 0 and not entry_objs[0].is_dead():
                    return entry_objs[0]
                
                link_url = p.get_protocol_url("http")
                link_url = link_url.replace("www.", "")
                entry_objs = objects.filter(link=link_url)

                if entry_objs.count() > 0 and not entry_objs[0].is_dead():
                    return entry_objs[0]

            link_https = p.get_protocol_url("https")
            https_objs = objects.filter(link=link_https)

            if https_objs.count() > 0 and not https_objs[0].is_dead():
                return https_objs[0]

            link_http = p.get_protocol_url("http")
            http_objs = objects.filter(link=link_http)

            if http_objs.count() > 0 and not http_objs[0].is_dead():
                return http_objs[0]

            """
            If both are dead - return https
            """

            if https_objs.count() > 0:
                return https_objs[0]
            if http_objs.count() > 0:
                return http_objs[0]

        objs = objects.filter(link=self.link)
        if objs.exists():
            return objs[0]

    def create(self, link_data):
        self.date = link_data["date_published"]
        is_archive = self.is_archive()
        if "bookmarked" in link_data and link_data["bookmarked"]:
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

        # TODO remove hardcoded links
        if (
            "title" in link_data
            and link_data["title"]
            and len(link_data["title"]) > 999
        ):
            link_data["title"] = link_data["title"][:998]
        if (
            "description" in link_data
            and link_data["description"]
            and len(link_data["description"]) > 999
        ):
            link_data["description"] = link_data["description"][:998]

        if "id" in link_data:
            del link_data["id"]

        try:
            if not is_archive:
                ob = LinkDataController.objects.create(**link_data)

            elif is_archive:
                ob = ArchiveLinkDataController.objects.create(**link_data)
        except Exception as E:
            AppLogging.exc(E, "Link data:{}".format(link_data))
            return

        if ob:
            u = EntryUpdater(ob)
            u.reset_local_data()

        return ob

    def move_to_archive(self):
        entry_obj = self.entry
        link = entry_obj.link

        objs = ArchiveLinkDataController.objects.filter(link=entry_obj.link)

        if objs.count() == 0:
            themap = entry_obj.get_map()
            themap["source_obj"] = entry_obj.source_obj
            themap["domain_obj"] = entry_obj.domain_obj
            try:
                archive_obj = ArchiveLinkDataController.objects.create(**themap)
                entry_obj.delete()
                return archive_obj

            except Exception as E:
                AppLogging.exc(E, "Cannot move to archive {}".format(link))
        else:
            try:
                entry_obj.delete()
            except Exception as E:
                AppLogging.exc(E, "Cannot delete entry {}".format(link))

    def move_from_archive(self):
        archive_obj = self.entry
        link = archive_obj.link

        objs = LinkDataController.objects.filter(link=archive_obj.link)
        if objs.count() == 0:
            themap = archive_obj.get_map()
            themap["source_obj"] = archive_obj.source_obj
            themap["domain_obj"] = archive_obj.domain_obj
            try:
                new_obj = LinkDataController.objects.create(**themap)
                archive_obj.delete()
                return new_obj

            except Exception as E:
                AppLogging.exc(E, "Canont move link to archive {}".format(link))
        else:
            try:
                archive_obj.delete()
            except Exception as E:
                AppLogging.exc(E, "Canont move link to archive {}".format(link))


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

        UserBookmarks.add(request.user, entry)

        if request.user.is_staff:
            entry.make_bookmarked()

        return entry

    def make_not_bookmarked(self, request):
        entry = self.entry

        UserBookmarks.remove(request.user, entry)

        is_bookmarked = UserBookmarks.is_bookmarked(entry)

        if not is_bookmarked:
            entry.make_not_bookmarked()
            self.evaluate()

        return entry

    def evaluate(self):
        """
        TODO rename to update()

        Checks:
         - if entry should be removed due to config accept_domains
         - updates permanent
         - if entry should be moved to archive
        """
        config = Configuration.get_object().config_entry

        entry = self.entry
        if not entry:
            return

        p = DomainAwarePage(entry.link)
        is_domain = p.is_domain()

        if not config.accept_not_domain_entries:
            if is_domain and config.accept_domains:
                pass
            elif not is_domain and config.accept_domains:
                """
                tags and votes, are deleted automatically
                """
                entry.delete()
                self.entry = None
                return
            elif entry.bookmarked:
                pass
            else:
                entry.delete()
                self.entry = None
                return

        if not entry.should_entry_be_permanent():
            entry.permament = False
        else:
            entry.permament = True
        entry.save()

        if not entry.is_permanent():
            if entry.is_remove_time():
                entry.delete()
                self.entry = None
            elif entry.is_archive_time():
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

        from ..models import UserTags, UserVotes, LinkCommentDataModel, UserBookmarks, UserEntryVisitHistory, UserEntryTransitionHistory

        source_entry = self.entry

        UserTags.move_entry(source_entry, destination_entry)
        UserVotes.move_entry(source_entry, destination_entry)
        LinkCommentDataModel.move_entry(source_entry, destination_entry)
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
        destination_entries = LinkDataController.objects.filter(link = destination_url)

        if destination_entries.count() > 0:
            return self.move_entry(destination_entries[0])
        else:
            self.entry.link = destination_url
            self.entry.save()

            return self.entry

    def is_archive(self):
        is_archive = BaseLinkDataController.is_archive_by_date(self.date)
        return is_archive

    def check_https_http_availability(self):
        """
        TODO - we should use EntryUrlInterface to check if we receive valid
        information.
        Some information might be missing in https:// version of a site

        @returns new object, or None object has not been changed
        """
        if not self.entry:
            return

        self.check_https_http_availability_entries()

        entry = self.entry

        c = Configuration.get_object().config_entry
        if not c.prefer_https:
            return

        if entry.is_https():
            http_url = entry.get_http_url()

            p = RequestBuilder(url = entry.link)
            ping_status = p.ping()

            if not ping_status:
                p = RequestBuilder(url = http_url)
                new_ping_status = p.ping()

                if new_ping_status:
                    return EntryWrapper(entry=entry).move_entry_to_url(http_url)

            return self.entry

        if entry.is_http():
            https_url = entry.get_https_url()

            p = RequestBuilder(https_url)
            new_ping_status = p.ping()

            if new_ping_status:
                return EntryWrapper(entry=entry).move_entry_to_url(https_url)

        return self.entry

    def check_www_nonww_availability(self):
        """
        TODO - we should use EntryUrlInterface to check if we receive valid
        information.
        Some information might be missing in https:// version of a site

        @returns new object, or None if object has not been changed
        """
        if not self.entry:
            return

        self.check_www_nonww_availability_entries()

        c = Configuration.get_object().config_entry

        if not c.prefer_non_www_sites:
            return

        entry = self.entry
        p = DomainAwarePage(entry.link)
        domain_only = p.get_domain_only()
        if not domain_only.startswith("www."):
            return

        destination_link = entry.link.replace("www.", "")

        p = RequestBuilder(url = destination_link)
        if p.ping():
            self.move_entry_to_url(destination_link)

        return self.entry

    def check_https_http_availability_entries(self):
        """
        Removes http<>https duplicates, if we have http and https pages select https to be present
        """
        entry = self.entry

        if entry.is_https():
            http_url = entry.get_http_url()

            http_entries = LinkDataController.objects.filter(link=http_url)
            if http_entries.count() != 0:
                w = EntryWrapper(entry = http_entries[0])
                w.move_entry(entry)

        if entry.is_http():
            https_url = entry.get_https_url()

            # if we have both, destroy http entry
            https_entries = LinkDataController.objects.filter(link=https_url)
            if https_entries.count() != 0:
                self.move_entry(https_entries[0])

        return self.entry

    def check_www_nonww_availability_entries(self):
        """
        Removes non-www and www pages duplicates.
        """
        entry = self.entry

        p = DomainAwarePage(entry.link)

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
        allow_recursion=True,
        ignore_errors=False,
    ):
        self.link = link
        self.link_data = link_data
        self.source_is_auto = source_is_auto
        self.allow_recursion = allow_recursion

        self.ignore_errors = ignore_errors
        c = Configuration.get_object().config_entry
        if c.accept_dead:
            self.ignore_errors = True

        self.result = None

        if self.link:
            self.add_from_link()

        if self.link_data:
            self.add_from_props(ignore_errors=self.ignore_errors)

    def add_from_link(self, ignore_errors=False):
        from ..pluginurl import UrlHandler

        """
        TODO extract this to a separate class?
        """
        self.ignore_errors = ignore_errors
        self.link = UrlHandler.get_cleaned_link(self.link)
        if not self.link:
            return

        p = DomainAwarePage(self.link)
        if p.is_link_service():
            return self.add_from_link_service()
        else:
            return self.add_from_normal_link()

    def add_from_link_service(self):
        from ..pluginurl import EntryUrlInterface

        url = EntryUrlInterface(self.link, ignore_errors=self.ignore_errors)
        link_data = url.get_props()
        if not link_data:
            if Configuration.get_object().config_entry.debug_mode:
                AppLogging.debug(
                    'Could not obtain properties for:<a href="{}">{}</a>'.format(
                        self.get_absolute_url(), self.link
                    )
                )
            return

        self.link_data = link_data
        return self.add_from_props(ignore_errors=self.ignore_errors)

    def add_from_normal_link(self):
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
            return

        url = EntryUrlInterface(self.link, ignore_errors=self.ignore_errors)
        link_data = url.get_props()
        if not link_data:
            if Configuration.get_object().config_entry.debug_mode:
                AppLogging.debug(
                    'Could not obtain properties for:<a href="{}">{}</a>'.format(
                        self.link, self.link
                    )
                )
            return

        # we obtain links from various places. We do not want technical links with no data, redirect, CDN or other
        if not self.is_link_data_valid_for_auto_add(link_data):
            return

        self.merge_link_data(link_data)

        if self.link_data:
            return self.add_from_props_internal()
        else:
            if Configuration.get_object().config_entry.debug_mode:
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
        if not self.is_property_set(link_data, "title"):
            return False
        if not self.is_property_set(link_data, "description"):
            return False

        return True

    def add_from_props(self, ignore_errors=False):
        from ..pluginurl import UrlHandler

        self.ignore_errors = ignore_errors

        url = self.link_data["link"]
        if not url:
            return

        obj = None

        self.link_data["link"] = UrlHandler.get_cleaned_link(self.link_data["link"])
        self.link = self.link_data["link"]

        wrapper = EntryWrapper(link=self.link)
        entry = wrapper.get()
        if entry:
            self.result = entry
            return entry

        entry = self.add_from_props_internal()
        self.result = entry
        return entry

    def add_from_props_internal(self):
        from ..pluginurl import UrlPropertyValidator

        entry = None

        self.link_data = self.get_clean_link_data()

        keywords = Configuration.get_object().get_blocked_keywords()
        v = UrlPropertyValidator(properties=self.link_data, blocked_keywords=keywords)
        if not v.is_valid():
            LinkDatabase.error(
                "Rejecting:{}\nData:{}\n".format(
                    self.link_data["link"], self.link_data["description"]
                )
            )
            return

        # if self.source_is_auto:
        #    self.link_data["link"] = self.link_data["link"].lower()

        c = Configuration.get_object().config_entry
        if self.is_domain_link_data() and c.accept_domains and c.keep_domains:
            if c.accept_domains:
                self.link_data["permanent"] = True

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
        return LinkDataController.get_clean_data(props)

    def is_domain_link_data(self):
        link_data = self.link_data
        p = DomainAwarePage(link_data["link"])
        return p.get_domain() == link_data["link"]

    def add_entry_internal(self):
        link_data = self.link_data

        new_link_data = dict(link_data)
        if "date_published" not in new_link_data:
            new_link_data["date_published"] = DateUtils.get_datetime_now_utc()
        if "date_update_last" not in new_link_data:
            new_link_data["date_update_last"] = DateUtils.get_datetime_now_utc()

        if "description" in new_link_data and new_link_data["description"] != None:
            new_link_data["description"] = LinkDataController.get_description_safe(
                new_link_data["description"]
            )

        if (
            "page_rating" not in new_link_data
            or "page_rating" in new_link_data
            and new_link_data["page_rating"] == 0
        ):
            if "page_rating_contents" in new_link_data:
                new_link_data["page_rating"] = new_link_data["page_rating_contents"]

        AppLogging.debug("Adding link: {}".format(new_link_data["link"]))

        wrapper = EntryWrapper(
            link=new_link_data["link"], date=new_link_data["date_published"]
        )

        return wrapper.create(new_link_data)

    def set_domain_object(self):
        config = Configuration.get_object().config_entry

        if config.enable_domain_support:
            domain = DomainsController.add(self.link_data["link"])

            if domain:
                self.link_data["domain_obj"] = domain
        return self.link_data

    def check_and_set_source_object(self):
        link_data = self.link_data

        if "source_obj" not in link_data and "source" in link_data:
            source_obj = None
            sources = SourceDataController.objects.filter(url=link_data["source"])
            if sources.exists():
                source_obj = sources[0]

            link_data["source_obj"] = source_obj

        return link_data

    def is_enabled_to_store(self):
        # manual entry is always enabled
        if not self.source_is_auto:
            return True

        config = Configuration.get_object().config_entry
        link = self.link_data["link"]

        p = DomainAwarePage(link)
        is_domain = p.is_domain()
        domain = p.get_domain_only()

        if not config.accept_not_domain_entries:
            if is_domain and config.accept_domains:
                pass
            elif not is_domain and config.accept_domains:
                return False
            elif "bookmarked" in self.link_data and self.link_data["bookmarked"]:
                pass
            else:
                return False

        # we do not store link services, we can store only what is behind those links
        p = DomainAwarePage(link)
        if p.is_link_service():
            return False

        # heavier checks last
        if self.is_live_video():
            return False

        if not config.accept_ip_addresses:
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

        self.add_sub_links()
        self.add_keywords()
        self.add_domain()

        if entry:
            self.download_thumbnail(entry.thumbnail)

    def add_domain(self):
        url = DomainAwarePage(self.link_data["link"]).get_domain()
        entries = LinkDataController.objects.filter(link=url)
        if entries.count() == 0:
            if "source_obj" in self.link_data:
                BackgroundJobController.link_add(
                    url=url, source=self.link_data["source_obj"]
                )
            else:
                BackgroundJobController.link_add(url=url)

    def download_thumbnail(self, thumbnail_path):
        if thumbnail_path:
            config = Configuration.get_object().config_entry
            if config.auto_store_thumbnails:
                BackgroundJobController.download_file(thumbnail_path)

    def add_sub_links(self):
        """
        Adds links from description of that link.
        Store link as-is.
        """
        if not self.allow_recursion:
            """
            We cannot allow to undefinitely traverse Internet and find all domains
            """
            return

        link_data = self.link_data

        config = Configuration.get_object().config_entry

        if config.accept_not_domain_entries or config.accept_domains:
            links = set()

            if config.accept_domains:
                p = DomainAwarePage(link_data["link"])
                domain = p.get_domain()
                links.add(domain)

            if config.auto_scan_entries:
                if "description" in link_data:
                    parser = ContentLinkParser(
                        link_data["link"], link_data["description"]
                    )
                    description_links = parser.get_links()

                    for link in description_links:
                        links.add(link)

                if "contents" in link_data:
                    parser = ContentLinkParser(link_data["link"], link_data["contents"])
                    contents_links = parser.get_links()

                    for link in contents_links:
                        links.add(link)

            for link in links:
                if "source_obj" in link_data:
                    BackgroundJobController.link_add(
                        url=link, source=link_data["source_obj"]
                    )
                else:
                    BackgroundJobController.link_add(url=link)

    def add_keywords(self):
        link_data = self.link_data

        config = Configuration.get_object().config_entry

        if config.enable_keyword_support:
            if "title" in link_data:
                KeyWords.add_link_data(link_data)

    def read_domains_from_bookmarks():
        objs = LinkDataController.objects.filter(bookmarked=True)
        for obj in objs:
            p = DomainAwarePage(obj.link)
            EntryDataBuilder(link=p.get_domain())


class EntriesCleanupAndUpdate(object):
    def cleanup(self, limit_s = 0):
        start_processing_time = time.time()

        cleanup = EntriesCleanup(archive_cleanup=False, start_processing_time=start_processing_time)
        if not cleanup.cleanup(limit_s):
            return False

        cleanup = EntriesCleanup(archive_cleanup=True, start_processing_time=start_processing_time)
        if not cleanup.cleanup(limit_s):
            return False

        # indicate that all has been finished correctly
        return True
