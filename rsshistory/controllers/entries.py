from datetime import datetime, date, timedelta
import os
import traceback
import time

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    BaseLinkDataModel,
    BaseLinkDataController,
    LinkDataModel,
    ArchiveLinkDataModel,
    AppLogging,
    SourceDataModel,
    KeyWords,
    UserTags,
    UserBookmarks,
)
from .sources import SourceDataController
from ..configuration import Configuration
from ..webtools import BasePage, HtmlPage, RssPage, ContentLinkParser, DomainAwarePage
from ..apps import LinkDatabase
from ..dateutils import DateUtils


class LinkDataController(LinkDataModel):
    class Meta:
        proxy = True

    def get_source_obj(self):
        if self.source_obj:
            return SourceDataController.objects.get(id=self.source_obj.id)
        else:
            return None

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse("{}:entry-detail".format(LinkDatabase.name), args=[str(self.id)])

    def get_edit_url(self):
        """Returns the URL to access a particular author instance."""

        return reverse("{}:entry-edit".format(LinkDatabase.name), args=[str(self.id)])

    def get_bookmark_set_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-bookmark".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_bookmark_unset_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-notbookmark".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_dead_url(self):
        if self.is_dead():
            """Returns the URL to access a particular author instance."""
            return reverse(
                "{}:entry-not-dead".format(LinkDatabase.name), args=[str(self.id)]
            )
        else:
            return reverse(
                "{}:entry-dead".format(LinkDatabase.name), args=[str(self.id)]
            )

    def get_title_safe(self):
        title = self.title
        if title:
            title = title.replace('"', "")
            title = title.replace("'", "")

        return title

    def get_search_term(self):
        term = ""

        title = self.get_title_safe()
        if title and title != "":
            if term != "":
                term += " "
            term += title

        if self.album and self.album != "" and term.find(self.album) == -1:
            term = self.album + " " + term

        if self.artist and self.artist != "" and term.find(self.artist) == -1:
            term = self.artist + " " + term

        term.strip()

        return term

    def get_remove_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse("{}:entry-remove".format(LinkDatabase.name), args=[str(self.id)])

    def cleanup(limit_s=0):
        """
        We do not want to starve other threads.
        Add limit, so that we can exit from cleanup thread
        """

        # TODO Move to link wrapper
        moved_all = LinkDataWrapper.move_old_links_to_archive(limit_s)
        cleared_all = LinkDataWrapper.clear_old_entries(limit_s)
        # LinkDataController.recreate_from_domains()
        LinkDataController.update_some_page_ratings()

        # TODO if configured to store domains, but do not store entries - remove all normal non-domain entries

        # indicate that all has been finished correctly
        return moved_all and cleared_all

    def recreate_from_domains():
        from .domains import DomainsController

        domains = DomainsController.objects.all()
        for domain in domains:
            full_domain = "https://" + domain.domain
            entries = LinkDataController.objects.filter(link=full_domain)
            if not entries.exist():
                from .backgroundjob import BackgroundJobController

                LinkDatabase.info("Creating entry for domain:{}".format(full_domain))
                BackgroundJobController.link_add(full_domain)

    def update_some_page_ratings():
        """
        TODO Remove this when database is cleaned up
        """
        from .backgroundjob import BackgroundJobController

        zeros = LinkDataController.objects.filter(
            page_rating=0, page_rating_contents__gt=0
        )
        for zero in zeros:
            zero.page_rating = zero.page_rating_contents
            zero.save()

        real_zeros = LinkDataController.objects.filter(
            page_rating=0, page_rating_contents=0
        )
        for zero in real_zeros[:1000]:
            BackgroundJobController.entry_update_data(zero)

    def get_full_information(data):
        from ..pluginurl.entryurlinterface import EntryUrlInterface

        info = EntryUrlInterface(data["link"], log=True, ignore_errors=True).get_props()
        return info

    def get_clean_data(props):
        from ..pluginurl import UrlHandler

        result = {}
        test = LinkDataController()

        for key in props:
            if hasattr(test, key):
                result[key] = props[key]

        if "link" in result:
            result["link"] = UrlHandler.get_cleaned_link(result["link"])

        if "tags" in result:
            del result["tags"]
        if "comments" in result:
            del result["comments"]
        if "vote" in result:
            del result["vote"]

        return result

    def tag(self, tags, user):
        """
        TODO Change this API to set_tags
        """
        data = {"user": user, "tags": tags, "entry": self}
        return UserTags.set_tags_map(data)

    def set_tag(self, tag_name, user):
        """
        TODO Change this API to add_tag
        """
        return UserTags.set_tag(self, tag_name, user)

    def vote(self, vote):
        self.page_rating_votes = vote
        self.save()

    def is_delete_time(self):
        conf = Configuration.get_object().config_entry
        if conf.days_to_remove_links == 0:
            return False

        day_to_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)

        return self.date_published < day_to_remove

    def is_archive_time(self):
        conf = Configuration.get_object().config_entry
        if conf.days_to_move_to_archive == 0:
            return False

        day_to_move = DateUtils.get_days_before_dt(conf.days_to_move_to_archive)

        return self.date_published < day_to_move


class ArchiveLinkDataController(ArchiveLinkDataModel):
    class Meta:
        proxy = True

    def get_source_obj(self):
        if self.source_obj:
            return SourceDataController.objects.get(id=self.source_obj.id)
        else:
            return None

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""

        return reverse(
            "{}:entry-archived".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_edit_url(self):
        """Returns the URL to access a particular author instance."""

        return reverse(
            "{}:entry-archive-edit".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_bookmark_set_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-bookmark".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_bookmark_unset_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-notbookmark".format(LinkDatabase.name),
            args=[str(self.id)],
        )

    def get_hide_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-hide".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_remove_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-remove".format(LinkDatabase.name), args=[str(self.id)]
        )


class LinkDataWrapper(object):
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
                ob = ArchiveLinkDataModel.objects.create(**link_data)
        except Exception as E:
            error_text = traceback.format_exc()
            AppLogging.error("Cannot create entry {}".format(error_text))
            return

        return ob

    def move_to_archive(entry_obj):
        objs = ArchiveLinkDataModel.objects.filter(link=entry_obj.link)

        if objs.count() == 0:
            themap = entry_obj.get_map()
            themap["source_obj"] = entry_obj.get_source_obj()
            themap["domain_obj"] = entry_obj.domain_obj
            try:
                archive_obj = ArchiveLinkDataModel.objects.create(**themap)
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
        start_processing_time = time.time()

        while True:
            entry = LinkDataWrapper.get_next_link_to_move_to_archive()
            # no more entries to process, cleaned up everything
            if not entry:
                return True

            if entry.is_delete_time():
                LinkDatabase.info("Deleting link: {}".format(entry.link))
                entry.delete()
                continue

            LinkDatabase.info("Moving link to archive: {}".format(entry.link))
            LinkDataWrapper.move_to_archive(entry)

            if limit_s > 0:
                passed_seconds = time.time() - start_processing_time
                if passed_seconds >= 60 * 10:
                    LinkDatabase.info("Task exeeded time:{}".format(passed_seconds))
                    return False

            """
            Do not remove one after another. Let the processor rest a little bit. He's tired you now?
            Do not starve other processes.
            """
            time.sleep(0.5)

    def get_next_link_to_move_to_archive():
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

        return entries[0]

    def clear_old_entries(limit_s=0):
        start_processing_time = time.time()

        print("Clearing for old entries")

        sources = SourceDataController.objects.all()
        for source in sources:
            while True:
                entry = LinkDataWrapper.get_next_source_entry_to_remove(source)

                if not entry:
                    break

                LinkDatabase.info("Removing link:{}".format(entry.link))

                entry.delete()

                if limit_s != 0:
                    passed_seconds = time.time() - start_processing_time
                    if passed_seconds >= 60 * 10:
                        LinkDatabase.info("Task exeeded time:{}".format(passed_seconds))
                        return False

                time.sleep(0.5)

        print("Clearing normal links")
        while True:
            entry = LinkDataWrapper.get_next_entry_to_remove()

            if not entry:
                break

            LinkDatabase.info("Removing link:{}".format(entry.link))

            entry.delete()

            if limit_s != 0:
                passed_seconds = time.time() - start_processing_time
                if passed_seconds >= 60 * 10:
                    LinkDatabase.info("Task exeeded time:{}".format(passed_seconds))
                    return False

            time.sleep(0.5)

        print("Clearing archive links")
        while True:
            entry = LinkDataWrapper.get_next_archive_entry_to_remove()

            if not entry:
                break

            LinkDatabase.info("Removing link:{}".format(entry.link))

            entry.delete()

            if limit_s != 0:
                passed_seconds = time.time() - start_processing_time
                if passed_seconds >= 60 * 10:
                    LinkDatabase.info("Task exeeded time:{}".format(passed_seconds))
                    return False

        return True

    def get_next_source_entry_to_remove(source):
        config = Configuration.get_object().config_entry
        config_days = config.days_to_remove_links

        if not source.is_removeable():
            return

        days = source.get_days_to_remove()

        if config_days != 0 and days == 0:
            days = config_days
        if config_days != 0 and config_days < days:
            days = config_days

        if days > 0:
            days_before = DateUtils.get_days_before_dt(days)

            entries = LinkDataController.objects.filter(
                source=source.url,
                bookmarked=False,
                permanent=False,
                date_published__lt=days_before,
            ).order_by("date_published")

            if entries.exists():
                return entries[0]

    def get_next_entry_to_remove():
        config = Configuration.get_object().config_entry
        config_days = config.days_to_remove_links

        days = config_days
        if days != 0:
            days_before = DateUtils.get_days_before_dt(days)

            entries = LinkDataController.objects.filter(
                bookmarked=False,
                permanent=False,
                date_published__lt=days_before,
            )

            if entries.exists():
                return entries[0]

    def get_next_archive_entry_to_remove():
        config = Configuration.get_object().config_entry
        config_days = config.days_to_remove_links

        days = config_days
        if days != 0:
            days_before = DateUtils.get_days_before_dt(days)

            entries = ArchiveLinkDataController.objects.filter(
                date_published__lt=days_before,
            )

            if entries.exists():
                return entries[0]


class LinkDataBuilder(object):
    """
    - sometimes we want to call this object directly, sometimes it should be redirected to "add link background job"
    - we do not change data in here, we do not correct, we just follow it (I think that is what should be)
    - all subservent entries are added by background controller, handled in a separate task
    - we cannot spend too much time in builder from any context. This code should be possibly fast
    - if there is a possibility to not search it, we do not do it
    """

    def __init__(
        self, link=None, link_data=None, source_is_auto=True, allow_recursion=True, ignore_errors=False
    ):
        self.link = link
        self.link_data = link_data
        self.source_is_auto = source_is_auto
        self.allow_recursion = allow_recursion
        self.ignore_errors = ignore_errors

        self.result = None

        if self.link:
            self.add_from_link()

        if self.link_data:
            self.add_from_props(ignore_errors = self.ignore_errors)

    def add_from_link(self, ignore_errors=False):
        from ..pluginurl import UrlHandler

        self.ignore_errors = ignore_errors
        self.link = UrlHandler.get_cleaned_link(self.link)

        p = DomainAwarePage(self.link)
        if p.is_link_service():
            return self.add_from_link_service()
        else:
            return self.add_from_normal_link()

    def add_from_link_service(self):
        from ..pluginurl.entryurlinterface import EntryUrlInterface

        url = EntryUrlInterface(self.link, ignore_errors = self.ignore_errors)
        link_data = url.get_props()
        if not link_data:
            AppLogging.error('Could not obtain properties for:<a href="{}">{}</a>'.format(self.get_absolute_url(), self.link))
            return

        self.link_data = link_data
        return self.add_from_props(ignore_errors = self.ignore_errors)

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

        from ..pluginurl.entryurlinterface import EntryUrlInterface

        url = EntryUrlInterface(self.link, ignore_errors = self.ignore_errors)
        link_data = url.get_props()
        if not link_data:
            AppLogging.error('Could not obtain properties for:<a href="{}">{}</a>'.format(self.link, self.link))
            return

        if self.is_status_code_invalid():
            AppLogging.error('Cannot add link - page status invalid:<a href="{}">{}</a>'.format(self.link, self.link))
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
            AppLogging.error('Could not obtain properties for:<a href="{}">{}</a>'.format(self.link, self.link))

    def add_from_props(self, ignore_errors = False):
        self.ignore_errors = ignore_errors

        from ..pluginurl import UrlHandler

        url = self.link_data["link"]

        if self.is_status_code_invalid():
            AppLogging.error('Cannot add link - page status invalid:<a href="{}">{}</a>'.format(self.link, self.link))
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
        from .backgroundjob import BackgroundJobController
        from ..pluginurl import UrlPropertyValidator

        entry = None

        self.link_data = self.get_clean_link_data()

        v = UrlPropertyValidator(properties = self.link_data)
        if not v.is_valid():
            LinkDatabase.error("Url is not valid: {}".format(self.link_data["link"]))
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
        from .domains import DomainsController

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

        p = DomainAwarePage(self.link_data["link"])
        is_domain = p.is_domain()

        if not config.auto_store_entries:
            if is_domain and config.auto_store_domain_info:
                pass
            elif "bookmarked" in self.link_data and self.link_data["bookmarked"]:
                pass
            else:
                return False

        # we do not store link services, we can store only what is behind those links
        p = DomainAwarePage(self.link_data["link"])
        if p.is_link_service():
            return False

        # heavier checks last
        if self.is_live_video():
            return False

        return True

    def is_live_video(self):
        link_data = self.link_data

        if "live" in link_data and link_data["live"]:
            return link_data["live"]

        return False

    def add_addition_link_data(self):
        try:
            link_data = self.link_data

            self.add_sub_links()
            self.add_keywords()
            # self.add_sources()

        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.exc(
                "Could not process entry: Entry:{} {}; Exc:{}\n{}".format(
                    link_data["link"],
                    link_data["title"],
                    str(e),
                    error_text,
                )
            )
            LinkDatabase.info(error_text)

    def add_sub_links(self):
        """
        Adds links from description of that link.
        Store link as-is.
        """
        from .backgroundjob import BackgroundJobController

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
            from .sources import SourceDataBuilder

            SourceDataBuilder(link=rss_url).add_from_link()

    def read_domains_from_bookmarks():
        objs = LinkDataController.objects.filter(bookmarked=True)
        for obj in objs:
            p = DomainAwarePage(obj.link)
            LinkDataBuilder(link=p.get_domain())
