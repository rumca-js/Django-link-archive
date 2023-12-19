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

    def get_hide_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse("{}:entry-hide".format(LinkDatabase.name), args=[str(self.id)])

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
                obj = LinkDataHyperController.add_simple(full_domain)
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
                    obj = LinkDataHyperController.add_simple(new_link)
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
        from ..pluginentries.handlerurl import HandlerUrl

        url = HandlerUrl(data["link"])
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


class LinkDataHyperController(object):
    """
    Archive managment can be tricky. It is long to process entire archive.
    If there is a possiblity we do not search it, we do not add anything to it.
    """

    def add_simple(link_url, input_props=None):
        objs = LinkDataController.objects.filter(link=link_url)
        if objs.count() != 0:
            return objs[0]

        from ..pluginentries.handlerurl import HandlerUrl

        url = HandlerUrl(link_url)
        props = url.get_props()
        if props:
            return LinkDataHyperController.add_new_link_internal(props)
        else:
            LinkDatabase.info("Could not obtain properties for:{}".format(link_url))

    def add_new_link(link_data, source_is_auto=False):
        obj = None

        if link_data["link"].endswith("/"):
            link_data["link"] = link_data["link"][:-1]

        # Try with https more that with https
        if link_data["link"].startswith("http://"):
            link_data["link"] = link_data["link"].replace("http://", "https://")

        if not LinkDataHyperController.add_new_link_internal(link_data, source_is_auto):
            # Try with https more that with http
            link_data["link"] = link_data["link"].replace("https://", "http://")

            return LinkDataHyperController.add_new_link_internal(
                link_data, source_is_auto
            )

    def add_new_link_internal(link_data, source_is_auto=False):
        obj = None

        c = Configuration.get_object().config_entry
        if (
            LinkDataHyperController.is_domain_link_data(link_data)
            and c.auto_store_domain_info
        ):
            if c.auto_store_domain_info:
                link_data["permanent"] = True

        if LinkDataHyperController.is_enabled_to_store(link_data, source_is_auto):
            link_data = LinkDataHyperController.check_and_set_source_object(link_data)

            is_archive = LinkDataHyperController.is_link_data_for_archive(link_data)

            obj = LinkDataHyperController.get_entry_internal(link_data, is_archive)

            if obj:
                return obj

            obj = LinkDataHyperController.add_entry_internal(link_data, is_archive)

        LinkDataHyperController.add_addition_link_data(link_data)

        return obj

    def is_domain_link_data(link_data):
        p = BasePage(link_data["link"])
        return p.get_domain() == link_data["link"]

    def get_entry_internal(link_data, is_archive):
        if not is_archive:
            objs = LinkDataModel.objects.filter(link=link_data["link"])
            if objs.exists():
                return objs[0]
        else:
            objs = ArchiveLinkDataModel.objects.filter(link=link_data["link"])
            if objs.exists():
                return objs[0]

    def add_entry_internal(link_data, is_archive):
        from ..dateutils import DateUtils
        from .domains import DomainsController

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

        if not is_archive:
            ob = LinkDataModel.objects.create(**new_link_data)

        elif is_archive:
            ob = ArchiveLinkDataModel.objects.create(**new_link_data)

        return ob

    def is_link_data_for_archive(link_data):
        if "bookmarked" in link_data and link_data["bookmarked"]:
            return False

        is_archive = False
        if "date_published" in link_data:
            is_archive = BaseLinkDataController.is_archive_by_date(
                link_data["date_published"]
            )

        return is_archive

    def check_and_set_source_object(link_data):
        if "source_obj" not in link_data and "source" in link_data:
            source_obj = None
            sources = SourceDataController.objects.filter(url=link_data["source"])
            if sources.exists():
                source_obj = sources[0]

            link_data["source_obj"] = source_obj

        return link_data

    def is_enabled_to_store(link_data, source_is_auto):
        # manual entry is always enabled
        if not source_is_auto:
            return True

        config = Configuration.get_object().config_entry

        p = BasePage(link_data["link"])
        is_domain = p.is_domain()

        if not config.auto_store_entries:
            if is_domain and config.auto_store_domain_info:
                pass
            elif "bookmarked" in link_data and link_data["bookmarked"]:
                pass
            else:
                return False

        if LinkDataHyperController.is_live_video(link_data):
            LinkDatabase.info("Adding link: {}".format(link_data["link"]))
            return False

        return True

    def is_live_video(link_data):
        p = HtmlPage(link_data["link"])

        if p.is_youtube():
            from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

            handler = YouTubeVideoHandler(link_data["link"])
            if handler.get_video_code():
                handler.download_details()
                if not handler.is_valid():
                    return True

        return False

    def is_link(link):
        objs = LinkDataModel.objects.filter(link=link)
        if objs.exists():
            return True

        objs = ArchiveLinkDataModel.objects.filter(link=link)
        if objs.exists():
            return True

        return False

    def add_addition_link_data(link_data):
        try:
            LinkDataHyperController.add_domains(link_data)
            LinkDataHyperController.add_keywords(link_data)
            LinkDataHyperController.add_sources(link_data)

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

    def add_domains(link_data):
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
                LinkDataHyperController.add_simple(domain)

    def add_keywords(link_data):
        config = Configuration.get_object().config_entry

        if config.auto_store_keyword_info:
            if "title" in link_data:
                KeyWords.add_link_data(link_data)

    def add_sources(link_props):
        conf = Configuration.get_object().config_entry

        if not conf.auto_store_sources:
            return

        link = link_props["link"]
        if "contents" in link_props:
            html = HtmlPage(link, link_props["contents"])
        else:
            html = HtmlPage(link)

        props = html.get_properties()

        if "rss_urls" not in props:
            return

        if props["rss_urls"] is None:
            return

        rss_urls = props["rss_urls"]
        if len(rss_urls) == 0:
            return

        for rss_url in rss_urls:
            LinkDataHyperController.add_source(rss_url, link_props)

    def add_source(rss_url, link_props):
        conf = Configuration.get_object().config_entry

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        if SourceDataModel.objects.filter(url=rss_url).count() > 0:
            return

        if "contents" in link_props:
            parser = RssPage(rss_url, link_props["contents"])
        else:
            parser = RssPage(rss_url)

        d = parser.parse()
        if d is None:
            PersistentInfo.error("RSS is empty: rss_url:{0}".format(rss_url))
            return

        if len(d.entries) == 0:
            PersistentInfo.error("RSS no entries: rss_url:{0}".format(rss_url))
            return

        props = {}
        props["url"] = rss_url

        title = parser.get_title()
        if title:
            props["title"] = title
        if not title:
            props["title"] = link_props["title"]

        props["export_to_cms"] = True
        language = parser.get_language()
        if language:
            props["language"] = language
        thumnail = parser.get_thumbnail()
        if thumnail:
            props["favicon"] = thumnail
        props["on_hold"] = not conf.auto_store_sources_enabled
        props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
        props["remove_after_days"] = 2
        props["category"] = "New"
        props["subcategory"] = "New"

        try:
            SourceDataModel.objects.create(**props)
        except Exception as E:
            PersistentInfo.error("Exception {}".format(str(E)))

    def store_error_info(url, info):
        lines = traceback.format_stack()
        line_text = ""
        for line in lines:
            line_text += line

        PersistentInfo.error("Domain{};{};Lines:{}".format(url, info, line_text))

    def get_link_object(link, date=None):
        from ..dateutils import DateUtils

        conf = Configuration.get_object().config_entry

        if date is None:
            obj = LinkDataController.objects.filter(link=link)
            if obj.count() > 0:
                return obj[0]
            obj = ArchiveLinkDataController.objects.filter(link=link)
            if obj.count() > 0:
                return obj[0]

            return None

        is_archive = BaseLinkDataController.is_archive_by_date(date)

        if is_archive:
            obj = ArchiveLinkDataController.objects.filter(link=link)
            if obj.count() > 0:
                return obj[0]
        else:
            obj = LinkDataController.objects.filter(link=link)
            if obj.count() > 0:
                return obj[0]

    def make_bookmarked(request, entry):
        if entry.is_archive_entry():
            LinkDataHyperController.move_from_archive(entry)

        entry.make_bookmarked(request.user.username)
        return True

    def make_not_bookmarked(request, entry):
        entry.make_not_bookmarked(request.user.username)
        from ..dateutils import DateUtils

        days_diff = DateUtils.get_day_diff(entry.date_published)

        conf = Configuration.get_object().config_entry

        if days_diff > conf.days_to_move_to_archive:
            LinkDataHyperController.move_to_archive(entry)

        return True

    def move_to_archive(entry):
        objs = ArchiveLinkDataModel.objects.filter(link=entry.link)
        if objs.count() == 0:
            themap = entry.get_map()
            themap["source_obj"] = entry.get_source_obj()
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
                PersistentInfo.error("Cannot delete entry {}".format(error_text))

    def move_from_archive(entry):
        objs = LinkDataModel.objects.filter(link=entry.link)
        if objs.count() == 0:
            themap = entry.get_map()
            themap["source_obj"] = entry.get_source_obj()
            try:
                LinkDataModel.objects.create(**themap)
                entry.delete()
            except Exception as e:
                error_text = traceback.format_exc()
        else:
            try:
                entry.delete()
            except Exception as e:
                error_text = traceback.format_exc()

    def read_domains_from_bookmarks():
        objs = LinkDataModel.objects.filter(bookmarked=True)
        for obj in objs:
            p = BasePage(obj.link)
            LinkDataHyperController.add_simple(p.get_domain())

    def get_clean_description(link_data):
        import re

        # as per recommendation from @freylis, compile once only
        CLEANR = re.compile("<.*?>")

        cleantext = re.sub(CLEANR, "", link_data["description"])
        return cleantext
        # from bs4 import BeautifulSoup
        # cleantext = BeautifulSoup(link_data["description"], "lxml").text
        # return cleantext
