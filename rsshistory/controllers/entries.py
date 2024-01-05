from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    BaseLinkDataModel,
    BaseLinkDataController,
    LinkDataModel,
    LinkTagsDataModel,
    ArchiveLinkDataModel,
    PersistentInfo,
    SourceDataModel,
    KeyWords,
)
from .sources import SourceDataController
from ..configuration import Configuration
from ..webtools import BasePage, HtmlPage, RssPage, ContentLinkParser
from ..apps import LinkDatabase


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
        if self.dead:
            """Returns the URL to access a particular author instance."""
            return reverse(
                "{}:entry-not-dead".format(LinkDatabase.name), args=[str(self.id)]
            )
        else:
            return reverse(
                "{}:entry-dead".format(LinkDatabase.name), args=[str(self.id)]
            )

    def get_remove_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse("{}:entry-remove".format(LinkDatabase.name), args=[str(self.id)])

    def cleanup(limit=0):
        LinkDataController.move_old_links_to_archive(limit)
        LinkDataController.clear_old_entries(limit)
        # LinkDataController.replace_http_link_with_https()
        # LinkDataController.recreate_from_domains()

        # TODO if configured to store domains, but do not store entries - remove all normal non-domain entries

    def recreate_from_domains():
        from .domains import DomainsController

        domains = DomainsController.objects.all()
        for domain in domains:
            full_domain = "https://" + domain.domain
            entries = LinkDataController.objects.filter(link=full_domain)
            if not entries.exist():
                LinkDatabase.info("Creating entry for domain:{}".format(full_domain))
                b = LinkDataBuilder()
                b.link = full_domain
                obj = b.get_from_link()

                if not obj:
                    PersistentInfo.create(
                        "Irreversably removing domain:{}".format(domain.domain)
                    )
                    domain.delete()

    def replace_http_link_with_https():
        # TODO move tags

        entries = LinkDataController.objects.filter(link__icontains="http://")
        for entry in entries:
            link = entry.link
            new_link = link.replace("http://", "https://")

            new_entries = LinkDataController.objects.filter(link=new_link)
            if not new_entries.exists():
                try:
                    LinkDatabase.info(
                        "Replacing http with https for:{} {}".format(link, new_link)
                    )
                    b = LinkDataBuilder()
                    b.link = new_link
                    obj = b.get_from_link()

                    if obj:
                        LinkDatabase.info(
                            "Removing old for:{} {}".format(link, new_link)
                        )
                        if entry.link != obj.link:
                            entry.delete()
                    else:
                        LinkDatabase.info(
                            "Could not create - not Removing old for:{} {}".format(
                                link, new_link
                            )
                        )
                except Exception as E:
                    error_text = traceback.format_exc()
                    PersistentInfo.error(
                        "Cannot create https link:{}".format(error_text)
                    )
            else:
                LinkDatabase.info(
                    "New exists - removing old for:{} {}".format(link, new_link)
                )
                entry.delete()

    def move_old_links_to_archive(limit=0):
        from ..dateutils import DateUtils

        conf = Configuration.get_object().config_entry

        if conf.days_to_move_to_archive == 0:
            return

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)

        index = 0
        entries = LinkDataController.objects.filter(
            bookmarked=False, permanent=False, date_published__lt=days_before
        )

        if not entries.exists():
            return

        for entry in entries:
            LinkDatabase.info("Moving link to archive: {}".format(entry.link))

            LinkDataController.move_to_archive(entry)
            index += 1

            if limit and index > limit:
                break

    def move_to_archive(entry):
        objs = ArchiveLinkDataModel.objects.filter(link=entry.link)
        if objs.count() == 0:
            themap = entry.get_map()
            domain_obj = entry.domain_obj
            themap["source_obj"] = entry.get_source_obj()
            themap["domain_obj"] = domain_obj
            try:
                ArchiveLinkDataModel.objects.create(**themap)
                entry.delete()
            except Exception as e:
                error_text = traceback.format_exc()
                PersistentInfo.error("Cannot move to archive {}".format(error_text))
        else:
            try:
                entry.delete()
            except Exception as e:
                error_text = traceback.format_exc()
                PersistentInfo.error("Cannot move to archive {}".format(error_text))

    def get_full_information(data):
        from ..pluginentries.entryurlinterface import EntryUrlInterface

        url = EntryUrlInterface(data["link"])
        return url.get_props()

    def clear_old_entries(limit=0):
        from ..dateutils import DateUtils

        config = Configuration.get_object().config_entry
        config_days = config.days_to_remove_links

        index = 0

        sources = SourceDataController.objects.all()
        for source in sources:
            if not source.is_removeable():
                continue

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
                )
                if not entries.exists():
                    continue

                for entry in entries:
                    LinkDatabase.info("Removing link:{}".format(entry.link))

                    entry.delete()
                    index += 1
                    if limit and index > limit:
                        return

        days = config_days
        if days != 0:
            days_before = DateUtils.get_days_before_dt(days)

            entries = LinkDataController.objects.filter(
                bookmarked=False,
                permanent=False,
                date_published__lt=days_before,
            )

            if entries.exists():
                for entry in entries:
                    LinkDatabase.info("Removing link:{}".format(entry.link))

                    entry.delete()
                    index += 1

                    if limit and index > limit:
                        return

            entries = ArchiveLinkDataController.objects.filter(
                bookmarked=False,
                permanent=False,
                date_published__lt=days_before,
            )

            if entries.exists():
                for entry in entries:
                    LinkDatabase.info("Removing link:{}".format(entry.link))

                    entry.delete()
                    index += 1

                    if limit and index > limit:
                        return

    def get_clean_data(props):
        result = {}
        test = LinkDataController()

        for key in props:
            if hasattr(test, key):
                result[key] = props[key]

        if "link" in result and result["link"].endswith("/"):
            result["link"] = result["link"][:-1]

        if "tags" in result:
            del result["tags"]
        if "comments" in result:
            del result["comments"]
        if "vote" in result:
            del result["vote"]

        return result

    def tag(self, tags, author=None):
        data = {"author": author, "link": self.link, "tags": tags}
        return LinkTagsDataModel.save_tags_internal(data)

    def vote(self, vote):
        self.page_rating_votes = vote
        self.save()


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
        objs = ArchiveLinkDataModel.objects.filter(link=self.link)
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

        if not is_archive:
            ob = LinkDataModel.objects.create(**link_data)

        elif is_archive:
            ob = ArchiveLinkDataModel.objects.create(**link_data)

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
                PersistentInfo.error("Cannot move to archive {}".format(error_text))
        else:
            try:
                entry.delete()
            except Exception as e:
                error_text = traceback.format_exc()
                PersistentInfo.error("Cannot delete entry {}".format(error_text))

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
        if entry.is_archive_entry():
            entry = LinkDataWrapper.move_from_archive(entry)

        entry.make_bookmarked(request.user.username)
        return entry

    def make_not_bookmarked(request, entry):
        entry.make_not_bookmarked(request.user.username)
        from ..dateutils import DateUtils

        days_diff = DateUtils.get_day_diff(entry.date_published)

        conf = Configuration.get_object().config_entry

        if days_diff > conf.days_to_move_to_archive:
            return LinkDataWrapper.move_to_archive(entry)

        return entry

    def get_clean_description(link_data):
        import re

        # as per recommendation from @freylis, compile once only
        CLEANR = re.compile("<.*?>")

        cleantext = re.sub(CLEANR, "", link_data["description"])
        return cleantext
        # from bs4 import BeautifulSoup
        # cleantext = BeautifulSoup(link_data["description"], "lxml").text
        # return cleantext


class LinkDataBuilder(object):
    """
    Archive managment can be tricky. It is long to process entire archive.
    If there is a possiblity we do not search it, we do not add anything to it.
    """

    def __init__(self, link=None, link_data=None, source_is_auto=False):
        self.link = link
        self.link_data = link_data
        self.source_is_auto = source_is_auto

        if self.link:
            self.add_from_link()

        if self.link_data:
            self.add_from_props()

    def add_from_link(self):
        wrapper = LinkDataWrapper(self.link)
        obj = wrapper.get_from_operational_db()
        if obj:
            return obj

        if self.link.startswith("http://"):
            link = self.link.replace("http://", "https://")
            wrapper = LinkDataWrapper(link)
            obj = wrapper.get_from_operational_db()
            if obj:
                return obj

        from ..pluginentries.entryurlinterface import EntryUrlInterface

        url = EntryUrlInterface(self.link)
        link_data = url.get_props()

        # TODO update missing keys - do not replace them

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
            LinkDatabase.info("Could not obtain properties for:{}".format(self.link))

    def add_from_props(self):
        obj = None

        self.link = self.link_data["link"]

        wrapper = LinkDataWrapper(self.link)
        obj = wrapper.get_from_operational_db()
        if obj:
            return obj

        if self.link.startswith("http://"):
            link = self.link.replace("http://", "https://")
            wrapper = LinkDataWrapper(link)
            obj = wrapper.get_from_operational_db()
            if obj:
                return obj

        # Try with https more that with https
        if self.link_data["link"].startswith("http://"):
            self.link_data["link"] = self.link_data["link"].replace(
                "http://", "https://"
            )

        if not self.add_from_props_internal():
            # Try with https more that with http
            self.link_data["link"] = self.link_data["link"].replace(
                "https://", "http://"
            )

            return self.add_from_props_internal()

    def add_from_props_internal(self):
        obj = None

        self.link_data = self.get_clean_link_data()

        c = Configuration.get_object().config_entry
        if self.is_domain_link_data() and c.auto_store_domain_info:
            if c.auto_store_domain_info:
                self.link_data["permanent"] = True

        if self.is_enabled_to_store():
            self.link_data = self.check_and_set_source_object()

            date = None
            if "date_published" in self.link_data:
                date = self.link_data["date_published"]
            wrapper = LinkDataWrapper(self.link_data["link"], date)
            obj = wrapper.get()

            if obj:
                return obj

            obj = self.add_entry_internal()

        self.add_addition_link_data()

        return obj

    def get_clean_link_data(self):
        props = self.link_data
        return LinkDataController.get_clean_data(props)

    def is_domain_link_data(self):
        link_data = self.link_data
        p = BasePage(link_data["link"])
        return p.get_domain() == link_data["link"]

    def add_entry_internal(self):
        from ..dateutils import DateUtils
        from .domains import DomainsController

        link_data = self.link_data

        new_link_data = dict(link_data)
        if "date_published" not in new_link_data:
            new_link_data["date_published"] = DateUtils.get_datetime_now_utc()

        domain = DomainsController.add(new_link_data["link"])
        if domain:
            new_link_data["domain_obj"] = domain

        if new_link_data["description"] != None:
            new_link_data["description"] = new_link_data["description"][
                : BaseLinkDataController.get_description_length() - 2
            ]

        LinkDatabase.info("Adding link: {}".format(link_data["link"]))

        wrapper = LinkDataWrapper(link_data["link"], link_data["date_published"])
        return wrapper.create(new_link_data)

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

        p = BasePage(self.link_data["link"])
        is_domain = p.is_domain()

        if not config.auto_store_entries:
            if is_domain and config.auto_store_domain_info:
                pass
            elif "bookmarked" in self.link_data and self.link_data["bookmarked"]:
                pass
            else:
                return False

        if self.is_live_video():
            return False

        return True

    def is_live_video(self):
        from ..pluginentries.entryurlinterface import UrlHandler

        link_data = self.link_data

        if "link" in link_data and link_data["link"]:
            handler = UrlHandler.get(link_data["link"])
            if type(handler) is UrlHandler.youtube_video_handler:
                if handler.get_video_code():
                    handler.download_details()
                    if not handler.is_valid():
                        return True

        return False

    def add_addition_link_data(self):
        try:
            link_data = self.link_data

            self.add_domains()
            self.add_keywords()
            self.add_sources()

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "Could not process entry: Entry:{} {}; Exc:{}\n{}".format(
                    link_data["link"],
                    link_data["title"],
                    str(e),
                    error_text,
                )
            )
            LinkDatabase.info(error_text)

    def add_domains(self):
        link_data = self.link_data

        config = Configuration.get_object().config_entry
        if config.auto_store_domain_info:
            domains = set()

            p = BasePage(link_data["link"])
            domain = p.get_domain()
            domains.add(domain)

            parser = ContentLinkParser(link_data["link"], link_data["description"])
            description_links = parser.get_links()

            for link in description_links:
                ppp = BasePage(link)
                domain = ppp.get_domain()
                domains.add(domain)

            for domain in domains:
                LinkDataBuilder(link=domain)

    def add_keywords(self):
        link_data = self.link_data

        config = Configuration.get_object().config_entry

        if config.auto_store_keyword_info:
            if "title" in link_data:
                KeyWords.add_link_data(link_data)

    def add_sources(self):
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
            LinkSourceBuilder.add_source(rss_url, link_props)

    def read_domains_from_bookmarks():
        objs = LinkDataController.objects.filter(bookmarked=True)
        for obj in objs:
            p = BasePage(obj.link)
            LinkDataBuilder(link=p.get_domain())
