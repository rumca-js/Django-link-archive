from datetime import timedelta
import traceback
import time
import ipaddress

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    BaseLinkDataController,
    AppLogging,
    KeyWords,
    UserBookmarks,
)
from ..configuration import Configuration
from ..webtools import BasePage, HtmlPage, RssPage, ContentLinkParser, DomainAwarePage
from ..apps import LinkDatabase
from ..dateutils import DateUtils
from ..pluginurl import EntryUrlInterface
from ..pluginurl import UrlHandler
from ..pluginurl import UrlPropertyValidator
from .entries import LinkDataController, ArchiveLinkDataController
from .backgroundjob import BackgroundJobController
from .domains import DomainsController
from .sources import SourceDataBuilder
from .sources import SourceDataController


class EntriesCleanup(object):
    def __init__(self, archive_cleanup=False):
        self.archive_cleanup = archive_cleanup

    def cleanup(self):
        sources = SourceDataController.objects.all()
        for source in sources:
            entries = self.get_source_entries(source)
            if entries:
                entries.delete()

        entries = self.get_general_entries()
        if entries:
            entries.delete()

        entries = self.get_stale_entries()
        if entries:
            entries.delete()

    def get_source_entries(self, source):
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
        if config.keep_permament_items:
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
        if config.keep_permament_items:
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
        if config.keep_permament_items:
            condition &= Q(bookmarked=False, permanent=False)

        entries = LinkDataController.objects.filter(condition)

        if entries.exists():
            return entries


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
            self.entry.delete()
            return True

        if self.is_stale_and_dead_permanently():
            self.entry.delete()
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


class EntryUpdater(object):
    def __init__(self, entry):
        self.entry = entry

    def update_data(self):
        """
        Fetches new information about page, and uses valid fields to set this object,
        but only if current field is not set

         - status code and page rating is update always
         - title and description could have been set manually, we do not want to change that
         - some other fields should be set only if present in props
        """

        entry = self.entry

        url = EntryUrlInterface(entry.link)
        props = url.get_props()
        p = url.p

        # always update
        if url.p:
            entry.page_rating_contents = url.p.get_page_rating()
        if url.h:
            entry.status_code = url.h.get_status_code()
        entry.save()

        if not props or not url.p:
            self.handle_invalid_response(url)
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
            if not entry.thumbnail:
                entry.thumbnail = props["thumbnail"]

        if "language" in props and props["language"] is not None:
            if not entry.language:
                entry.language = props["language"]

        if "date_published" in props and props["date_published"] is not None:
            if not entry.date_published:
                entry.date_published = props["date_published"]

        entry.update_calculated_vote()

    def reset_data(self):
        """
        Fetches new information about page, and uses valid fields to set this object.

         - status code and page rating is update always
         - new data are changed only if new data are present at all
        """
        entry = self.entry

        url = EntryUrlInterface(entry.link)
        props = url.get_props()

        if url.p:
            entry.page_rating_contents = url.p.get_page_rating()
        if url.h:
            entry.status_code = url.h.get_status_code()
        entry.save()

        if not props or not url.p:
            self.handle_invalid_response(url)
            return

        if entry.date_dead_since:
            entry.date_dead_since = False

        if "title" in props and props["title"] is not None:
            entry.title = props["title"]

        if "description" in props and props["description"] is not None:
            entry.description = props["description"]

        if "thumbnail" in props and props["thumbnail"] is not None:
            entry.thumbnail = props["thumbnail"]

        if "language" in props and props["language"] is not None:
            entry.language = props["language"]

        # if "date_published" in props and props["date_published"] is not None:
        #    entry.date_published = props["date_published"]

        entry.save()

    def handle_invalid_response(self, url_entry_interface):
        entry = self.entry

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
            AppLogging.info(
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
    def update_entries(self):
        self.update_std_entries()
        self.update_stale_entries()

    def update_std_entries(self):
        c = Configuration.get_object()
        conf = c.config_entry

        if conf.days_to_check_stale_entries == 0:
            return

        date_to_check = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_check_std_entries
        )

        condition_days_to_check = Q(date_update_last__lt=date_to_check)
        condition_status_valid = Q(date_dead_since__isnull=True)

        max_limit_entries = 1000

        entries = LinkDataController.objects.filter(
            condition_days_to_check & condition_status_valid
        ).order_by("date_update_last")
        for entry in entries[:max_limit_entries]:
            # update entry - it is either alive - will be re-enabled, or removed
            BackgroundJobController.entry_update_data(entry)

    def update_stale_entries(self):
        c = Configuration.get_object()
        conf = c.config_entry

        if conf.days_to_check_stale_entries == 0:
            return

        date_to_check = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_check_stale_entries
        )

        condition_days_to_check = Q(date_update_last__lt=date_to_check)
        condition_status_invalid = Q(date_dead_since__isnull=False)

        max_limit_entries = 1000

        entries = LinkDataController.objects.filter(
            condition_days_to_check & condition_status_invalid
        ).order_by("date_update_last")
        for entry in entries[:max_limit_entries]:
            # update entry - it is either alive - will be re-enabled, or removed
            BackgroundJobController.entry_update_data(entry)


class LinkDataWrapper(object):
    """
    Perform actions for both -> normal, and archive
    """

    def __init__(self, link, date=None):
        self.link = link
        self.date = date

    def is_archive(self):
        is_archive = BaseLinkDataController.is_archive_by_date(self.date)
        return is_archive

    def get(self):
        if self.date:
            is_archive = self.is_archive()

            if not is_archive:
                obj = self.get_from_operational_db()
                if obj:
                    return obj
            else:
                obj = self.get_from_archive()
                if obj:
                    return obj

        else:
            obj = self.get_from_operational_db()
            if obj:
                return obj

            obj = self.get_from_archive()
            if obj:
                return obj

    def get_from_archive(self):
        objs = ArchiveLinkDataController.objects.filter(link=self.link)
        if objs.exists():
            return objs[0]

    def get_from_operational_db(self):
        objs = LinkDataController.objects.filter(link=self.link)
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
            error_text = traceback.format_exc()
            AppLogging.error("Cannot create entry {}".format(error_text))
            return

        return ob

    def move_to_archive(entry_obj):
        objs = ArchiveLinkDataController.objects.filter(link=entry_obj.link)

        if objs.count() == 0:
            themap = entry_obj.get_map()
            themap["source_obj"] = entry_obj.get_source_obj()
            themap["domain_obj"] = entry_obj.domain_obj
            try:
                archive_obj = ArchiveLinkDataController.objects.create(**themap)
                entry_obj.delete()
                return archive_obj

            except Exception as e:
                error_text = traceback.format_exc()
                AppLogging.error("Cannot move to archive {}".format(error_text))
        else:
            try:
                entry_obj.delete()
            except Exception as e:
                error_text = traceback.format_exc()
                AppLogging.error("Cannot delete entry {}".format(error_text))

    def move_from_archive(archive_obj):
        objs = LinkDataController.objects.filter(link=archive_obj.link)
        if objs.count() == 0:
            themap = archive_obj.get_map()
            themap["source_obj"] = archive_obj.get_source_obj()
            themap["domain_obj"] = archive_obj.domain_obj
            try:
                new_obj = LinkDataController.objects.create(**themap)
                archive_obj.delete()
                return new_obj

            except Exception as e:
                error_text = traceback.format_exc()
                LinkDatabase.error(error_text)
        else:
            try:
                entry.delete()
            except Exception as e:
                error_text = traceback.format_exc()

    def make_bookmarked(request, entry):
        """
        TODO move this API to UserBookmarks
        """
        UserBookmarks.add(request.user, entry)

        if entry.is_archive_entry():
            entry = LinkDataWrapper.move_from_archive(entry)

        if request.user.is_staff:
            entry.make_bookmarked()

        return entry

    def make_not_bookmarked(request, entry):
        UserBookmarks.remove(request.user, entry)

        is_bookmarked = UserBookmarks.is_bookmarked(entry)

        if not is_bookmarked:
            entry.make_not_bookmarked()

            if entry.is_archive_time():
                return LinkDataWrapper.move_to_archive(entry)

        return entry

    def get_clean_description(link_data):
        import re

        # remove any html tags
        CLEANR = re.compile("<.*?>")
        cleantext = re.sub(CLEANR, "", link_data["description"])

        return cleantext

    def move_old_links_to_archive(limit_s=0):
        """
        TODO Refactor this shit. I think we should operate on 'chunks' rather than entry-entry
        """
        start_processing_time = time.time()

        entries = LinkDataWrapper.get_links_to_move_to_archive()
        # no more entries to process, cleaned up everything
        if not entries:
            return True

        for entry in entries:
            LinkDatabase.info("Moving link to archive: {}".format(entry.link))
            LinkDataWrapper.move_to_archive(entry)

            if limit_s > 0:
                passed_seconds = time.time() - start_processing_time
                if passed_seconds >= 60 * 10:
                    LinkDatabase.info("Task exeeded time:{}".format(passed_seconds))
                    return False

    def get_links_to_move_to_archive():
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


class LinkDataBuilder(object):
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
        self.ignore_errors = ignore_errors
        self.link = UrlHandler.get_cleaned_link(self.link)

        p = DomainAwarePage(self.link)
        if p.is_link_service():
            return self.add_from_link_service()
        else:
            return self.add_from_normal_link()

    def add_from_link_service(self):
        url = EntryUrlInterface(self.link, ignore_errors=self.ignore_errors)
        link_data = url.get_props()
        if not link_data:
            AppLogging.error(
                'Could not obtain properties for:<a href="{}">{}</a>'.format(
                    self.get_absolute_url(), self.link
                )
            )
            return

        self.link_data = link_data
        return self.add_from_props(ignore_errors=self.ignore_errors)

    def is_status_code_invalid(self):
        if self.ignore_errors:
            return False

        if "status_code" in self.link_data:
            code = self.link_data["status_code"]
            return code >= 200 and code < 300

        return False

    def add_from_normal_link(self):
        wrapper = LinkDataWrapper(self.link)
        obj = wrapper.get_from_operational_db()
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
            AppLogging.error(
                'Could not obtain properties for:<a href="{}">{}</a>'.format(
                    self.link, self.link
                )
            )
            return

        if self.is_status_code_invalid():
            AppLogging.error(
                    'Cannot add link - page status invalid:<a href="{}">{}</a>\nData:{}'.format(
                    self.link, self.link, link_data
                )
            )
            return

        # TODO update missing keys - do not replace them
        new_link_data = None

        if self.link_data and link_data:
            new_link_data = {**self.link_data, **link_data}
        if self.link_data:
            new_link_data = self.link_data
        if link_data:
            new_link_data = link_data

        self.link_data = new_link_data

        if self.link_data:
            return self.add_from_props_internal()
        else:
            AppLogging.error(
                'Could not obtain properties for:<a href="{}">{}</a>'.format(
                    self.link, self.link
                )
            )

    def add_from_props(self, ignore_errors=False):
        self.ignore_errors = ignore_errors

        url = self.link_data["link"]

        if self.is_status_code_invalid():
            AppLogging.error(
                    'Cannot add link - page status invalid:<a href="{}">{}</a>\nData:{}'.format(
                    self.link, self.link, self.link_data
                )
            )
            return

        obj = None

        self.link_data["link"] = UrlHandler.get_cleaned_link(self.link_data["link"])
        self.link = self.link_data["link"]

        wrapper = LinkDataWrapper(self.link)
        entry = wrapper.get_from_operational_db()
        if entry:
            self.result = entry
            return entry

        entry = self.add_from_props_internal()
        self.result = entry
        return entry

    def add_from_props_internal(self):
        entry = None

        self.link_data = self.get_clean_link_data()

        v = UrlPropertyValidator(properties=self.link_data)
        if not v.is_valid():
            LinkDatabase.error("Rejecting:{}\nData:{}\n".format(self.link_data["link"], self.link_data["description"]))
            return

        # if self.source_is_auto:
        #    self.link_data["link"] = self.link_data["link"].lower()

        c = Configuration.get_object().config_entry
        if self.is_domain_link_data() and c.auto_store_domain_info:
            if c.auto_store_domain_info:
                self.link_data["permanent"] = True

        if self.is_enabled_to_store():
            date = None
            if "date_published" in self.link_data:
                date = self.link_data["date_published"]
            wrapper = LinkDataWrapper(self.link_data["link"], date)
            entry = wrapper.get()

            if entry:
                return entry

            self.link_data = self.check_and_set_source_object()
            self.link_data = self.set_domain_object()

            entry = self.add_entry_internal()

            # TODO if object just created
            if entry:
                c = Configuration.get_object().config_entry
                if c.auto_store_entries_use_clean_page_info:
                    BackgroundJobController.entry_reset_data(entry)
                elif c.auto_store_entries_use_all_data:
                    BackgroundJobController.entry_update_data(entry)

        self.add_addition_link_data()

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

        LinkDatabase.info("Adding link: {}".format(new_link_data["link"]))

        wrapper = LinkDataWrapper(
            new_link_data["link"], new_link_data["date_published"]
        )

        return wrapper.create(new_link_data)

    def set_domain_object(self):
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

        if not config.auto_store_entries:
            if is_domain and config.auto_store_domain_info:
                pass
            elif not is_domain and config.auto_store_domain_info:
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

    def add_addition_link_data(self):
        link_data = self.link_data

        self.add_sub_links()
        self.add_keywords()
        self.add_domain()
        # self.add_sources()

    def add_domain(self):
        url = DomainAwarePage(self.link_data["link"]).get_domain()
        entries = LinkDataController.objects.filter(link=url)
        if entries.count() == 0:
            BackgroundJobController.link_add(url)

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

        if config.auto_store_entries or config.auto_store_domain_info:
            links = set()

            if config.auto_store_domain_info:
                p = DomainAwarePage(link_data["link"])
                domain = p.get_domain()
                links.add(domain)

            if config.auto_scan_new_entries:
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
                BackgroundJobController.link_add(link)

    def add_keywords(self):
        link_data = self.link_data

        config = Configuration.get_object().config_entry

        if config.auto_store_keyword_info:
            if "title" in link_data:
                KeyWords.add_link_data(link_data)

    def add_sources(self):
        # TODO if it is RSS link (link_data["link"]), should we also add a source?

        link_props = self.link_data

        conf = Configuration.get_object().config_entry

        if not conf.auto_store_sources:
            return

        link = link_props["link"]
        if "contents" in link_props:
            html = HtmlPage(link, link_props["contents"])
        else:
            html = HtmlPage(link)

        rss_urls = html.get_rss_urls()

        for rss_url in rss_urls:
            SourceDataBuilder(link=rss_url).add_from_link()

    def read_domains_from_bookmarks():
        objs = LinkDataController.objects.filter(bookmarked=True)
        for obj in objs:
            p = DomainAwarePage(obj.link)
            LinkDataBuilder(link=p.get_domain())


class EntriesCleanupAndUpdate(object):
    def cleanup(self):
        cleanup = EntriesCleanup(archive_cleanup=False)
        cleanup.cleanup()
        cleanup = EntriesCleanup(archive_cleanup=True)
        cleanup.cleanup()

        # TODO Move to link wrapper
        moved_all = LinkDataWrapper.move_old_links_to_archive()

        updater = EntriesUpdater()
        updater.update_entries()

        # LinkDataController.recreate_from_domains()

        # indicate that all has been finished correctly
        return moved_all