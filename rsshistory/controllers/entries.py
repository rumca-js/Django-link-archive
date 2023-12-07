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


class EntryPageDataReader(object):
    def __init__(self, data):
        self.data = data
        self.p = HtmlPage(self.data["link"])

    def get_full_information(self):
        p = self.p

        if self.data["link"].endswith("/"):
            self.data["link"] = self.data["link"][:-1]

        conf = Configuration.get_object().config_entry
        if conf.auto_store_domain_info and p.get_domain() == self.data["link"]:
            self.data["permanent"] = True

        if p.is_html():
            self.data["page_rating_contents"] = p.get_page_rating()

        self.data["thumbnail"] = None

        if p.is_youtube():
            self.update_info_youtube()
        if p.is_html():
            self.update_info_html()
        if p.is_rss():
            self.update_info_rss()

        self.update_info_default()
        return self.data

    def update_info_youtube(self):
        # TODO there should be some generic handlers
        from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

        h = YouTubeVideoHandler(self.data["link"])
        h.download_details()
        if h.get_video_code() is None:
            return self.data

        if "source" not in self.data or self.data["source"].strip() == "":
            self.data["source"] = h.get_channel_feed_url()
        self.data["link"] = h.get_link_url()
        if "title" not in self.data or self.data["title"].strip() == "":
            self.data["title"] = h.get_title()
        # TODO limit comes from LinkDataModel, do not hardcode
        if "description" not in self.data or self.data["description"].strip() == "":
            self.data["description"] = h.get_description()[:900]
        self.data["date_published"] = h.get_datetime_published()
        if (
            "thumbnail" not in self.data
            or self.data["thumbnail"] is None
            or self.data["thumbnail"].strip() == ""
        ):
            self.data["thumbnail"] = h.get_thumbnail()
        self.data["artist"] = h.get_channel_name()
        self.data["album"] = h.get_channel_name()

        return self.data

    def update_info_html(self):
        p = self.p

        if "language" not in self.data or not self.data["language"]:
            self.data["language"] = p.get_language()
        if "title" not in self.data or not self.data["title"]:
            self.data["title"] = p.get_title()
        if "description" not in self.data or not self.data["description"]:
            self.data["description"] = p.get_title()

        return self.data

    def update_info_rss(self):
        r = RssPage(self.p.get_contents())
        # TODO add title and description handling
        return self.data

    def update_info_default(self):
        p = self.p

        if "source" not in self.data or not self.data["source"]:
            self.data["source"] = p.get_domain()
        if "artist" not in self.data or not self.data["artist"]:
            self.data["artist"] = p.get_domain()
        if "album" not in self.data or not self.data["album"]:
            self.data["album"] = p.get_domain()
        if "language" not in self.data or not self.data["language"]:
            self.data["language"] = ""
        if "title" not in self.data or not self.data["title"]:
            self.data["title"] = p.get_domain()
        if "description" not in self.data or not self.data["description"]:
            self.data["description"] = p.get_domain()

        sources = SourceDataModel.objects.filter(url=self.data["source"])
        if sources.count() > 0:
            self.data["artist"] = sources[0].title
            self.data["album"] = sources[0].title

        return self.data


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
            print(
                "[{}]:Moving link to archive: {}".format(LinkDatabase.name, entry.link)
            )

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
        reader = EntryPageDataReader(data)
        return reader.get_full_information()

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
                    print("[{}] Removing link:{}".format(LinkDatabase.name, entry.link))

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
                    print("[{}] Removing link:{}".format(LinkDatabase.name, entry.link))

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
                    print("[{}] Removing link:{}".format(LinkDatabase.name, entry.link))

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

    def add_new_link(link_data, source_is_auto=False):
        obj = None

        if link_data["link"].endswith("/"):
            link_data["link"] = link_data["link"][:-1]

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

            if not LinkDataHyperController.is_live_video(link_data):
                print(
                    "[{}] Adding link: {}".format(LinkDatabase.name, link_data["link"])
                )

                obj = LinkDataHyperController.add_entry_internal(link_data, is_archive)

        LinkDataHyperController.add_addition_link_data(link_data)

        return obj

    def add_simple(link_url):
        props = LinkDataHyperController.get_htmlpage_props(link_url, {})
        LinkDataHyperController.add_new_link(props)

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
        config = Configuration.get_object().config_entry

        if (
            "permanent" in link_data
            and link_data["permanent"]
            and config.auto_store_domain_info
        ):
            return True

        if source_is_auto and not config.auto_store_entries:
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

    def get_youtube_props(url, data):
        from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

        objs = LinkDataController.objects.filter(link=url)
        if objs.count() != 0:
            return False

        h = YouTubeVideoHandler(url)
        if not h.download_details():
            PersistentInfo.error("Could not obtain details for link:{}".format(url))
            return False

        link_data = {}
        source = h.get_channel_feed_url()
        if source is None:
            PersistentInfo.error("Could not obtain channel feed url:{}".format(url))
            return False

        link_data["link"] = h.get_link_url()
        link_data["title"] = h.get_title()
        link_data["description"] = h.get_description()
        link_data["date_published"] = h.get_datetime_published()
        link_data["thumbnail"] = h.get_thumbnail()
        link_data["artist"] = h.get_channel_name()

        language = "en"
        if "language" in data:
            link_data["language"] = data["language"]
        user = None
        if "user" in data:
            link_data["user"] = data["user"]
        bookmarked = False
        if "bookmarked" in data:
            link_data["bookmarked"] = data["bookmarked"]

        source_obj = None
        sources = SourceDataModel.objects.filter(url=source)
        if sources.exists():
            link_data["source_obj"] = sources[0]

    def get_htmlpage_props(url, output_map, source_obj=None):
        from ..dateutils import DateUtils

        link_ob = HtmlPage(url)

        if "link" not in output_map:
            output_map["link"] = url
        if "title" not in output_map:
            title = link_ob.get_title()
            output_map["title"] = title
        if "description" not in output_map:
            description = link_ob.get_description()
            if description is None:
                description = title
            output_map["description"] = description

        if "language" not in output_map:
            language = link_ob.get_language()
            if not language:
                if source_obj:
                    language = source_obj.language
            output_map["language"] = language

        if "date_published" not in output_map:
            output_map["date_published"] = DateUtils.get_datetime_now_utc()

        if "thumbnail" not in output_map:
            output_map["thumbnail"] = link_ob.get_image()

        if "source_obj" not in output_map and source_obj:
            output_map["source_obj"] = source_obj

        return output_map

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
            print(error_text)

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
        html = HtmlPage(link)
        props = html.get_properties_map()

        rss_url = props["rss_url"]
        if not rss_url:
            return

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        if SourceDataModel.objects.filter(url=rss_url).count() > 0:
            return

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
        props["export_to_cms"] = False
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
