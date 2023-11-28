from datetime import datetime, date, timedelta
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    ConfigurationEntry,
    BaseLinkDataModel,
    BaseLinkDataController,
    LinkDataModel,
    ArchiveLinkDataModel,
    BackgroundJob,
    PersistentInfo,
    ConfigurationEntry,
    SourceDataModel,
    SourceOperationalData,
    LinkCommentDataModel,
    LinkTagsDataModel,
    LinkVoteDataModel,
    Domains,
    KeyWords,
)

from ..configuration import Configuration
from ..webtools import BasePage, HtmlPage, RssPage, ContentLinkParser
from ..apps import LinkDatabase


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

    def add(source_data_map):
        sources = SourceDataController.objects.filter(url=source_data_map["url"])
        if sources.count() > 0:
            return None

        # TODO add domain when adding new source
        source = SourceDataController.objects.create(**source_data_map)

        SourceDataController.fix_entries(source)

        if Configuration.get_object().config_entry.auto_store_domain_info:
            Domains.add(source_data_map["url"])

        return source

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:source-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_days_to_remove(self):
        days = 0
        try:
            days = int(self.remove_after_days)
        except Exception as E:
            PersistentInfo.error("Exception {}".format(str(E)))

        return days

    def get_long_description(self):
        return "Category:{} Subcategory:{} Export:{} On Hold:{} Type:{}".format(
            self.category,
            self.subcategory,
            self.export_to_cms,
            self.on_hold,
            self.source_type,
        )

    def get_full_description(self):
        return "{} Export:{} Fetched:{} Number of entries:{} Import seconds:{}".format(
            self.get_long_description(),
            self.export_to_cms,
            self.get_date_fetched(),
            self.get_number_of_entries(),
            self.get_import_seconds(),
        )

    def is_fetch_possible(self):
        from ..dateutils import DateUtils

        if self.on_hold:
            return False

        now = DateUtils.get_datetime_now_utc()
        date_fetched = self.get_date_fetched()

        if date_fetched:
            time_since_update = now - date_fetched
            # mins = time_since_update / timedelta(minutes=1)
            secs = time_since_update / timedelta(seconds=1)

            if secs >= self.fetch_period:
                return True
            return False

        return True

    def is_removeable(self):
        days = self.get_days_to_remove()

        if days > 0:
            return True
        else:
            return False

    def get_op_data(self):
        if hasattr(self, "dynamic_data"):
            return self.dynamic_data

    def get_date_fetched(self):
        obj = self.get_op_data()
        if obj:
            return obj.date_fetched

    def get_page_hash(self):
        obj = self.get_op_data()
        if obj:
            return obj.page_hash

    def get_import_seconds(self):
        obj = self.get_op_data()
        if obj:
            return obj.import_seconds

    def get_number_of_entries(self):
        obj = self.get_op_data()
        if obj:
            return obj.number_of_entries

    def set_operational_info(
        self, date_fetched, number_of_entries, import_seconds, hash_value
    ):
        obj = self.get_op_data()
        if obj:
            obj.date_fetched = date_fetched
            obj.import_seconds = import_seconds
            obj.number_of_entries = number_of_entries
            obj.page_hash = hash_value
            obj.save()
        else:
            # previously we could have dangling data without relation
            op_datas = SourceOperationalData.objects.filter(url=self.url)

            if op_datas.count() == 0:
                obj = SourceOperationalData(
                    url=self.url,
                    date_fetched=date_fetched,
                    import_seconds=import_seconds,
                    number_of_entries=number_of_entries,
                    page_hash=hash_value,
                    source_obj=self,
                )
                obj.save()
            else:
                obj = op_datas[0]
                obj.date_fetched = date_fetched
                obj.import_seconds = import_seconds
                obj.number_of_entries = number_of_entries
                obj.page_hash = hash_value
                obj.source_obj = self
                obj.save()

        return obj

    def get_favicon(self):
        if self.favicon:
            return self.favicon

        page = BasePage(self.url)
        domain = page.get_domain()
        return domain + "/favicon.ico"

    def get_domain(self):
        page = BasePage(self.url)
        return page.get_domain()

    def get_domain_only(self):
        page = BasePage(self.url)
        return page.get_domain_only()

    def get_export_names():
        return [
            "id",
            "url",
            "title",
            "category",
            "subcategory",
            "dead",
            "export_to_cms",
            "remove_after_days",
            "language",
            "favicon",
            "on_hold",
            "fetch_period",
            "source_type",
        ]

    def get_query_names():
        return [
            "id",
            "url",
            "title",
            "category",
            "subcategory",
            "dead",
            "export_to_cms",
            "remove_after_days",
            "language",
            "favicon",
            "on_hold",
            "fetch_period",
            "source_type",
        ]

    def get_map(self):
        output_data = {}

        export_names = SourceDataController.get_export_names()
        for export_name in export_names:
            val = getattr(self, export_name)
            output_data[export_name] = val

        return output_data

    def get_map_full(self):
        return self.get_map()

    def get_full_information(data):
        p = BasePage(data["url"])
        # TODO if passed url is youtube video, obtain information, obtain channel feed url

        if p.is_rss():
            print("Page is rss")
            return SourceDataController.get_info_from_rss(data["url"])
        elif p.is_youtube():
            from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

            print("Page is youtube")
            handler = YouTubeVideoHandler(data["url"])
            handler.download_details()
            return SourceDataController.get_info_from_rss(
                handler.get_channel_feed_url()
            )
        elif p.get_rss_url():
            p = HtmlPage(data["url"])
            print("Page has RSS url")
            return SourceDataController.get_info_from_rss(p.get_rss_url())
        else:
            print("Obtaining from page")
            return SourceDataController.get_info_from_page(data["url"], p)

    def get_info_from_rss(url):
        reader = RssPage(url)
        feed = reader.parse()

        data = {}
        data["url"] = url
        data["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
        title = reader.get_title()
        if title:
            data["title"] = title
        subtitle = reader.get_subtitle()
        if subtitle:
            data["description"] = subtitle
        language = reader.get_language()
        if language:
            data["language"] = language
        thumb = reader.get_thumbnail()
        if thumb:
            data["favicon"] = thumb
        return data

    def get_info_from_page(url, p):
        from ..pluginsources.sourceparseplugin import BaseParsePlugin

        data = {}
        data["url"] = url
        data["source_type"] = BaseParsePlugin.PLUGIN_NAME
        data["language"] = p.get_language()
        data["title"] = p.get_title()
        data["description"] = p.get_title()
        data["page_rating"] = p.get_page_rating()
        return data

    def get_channel_page_url(self):
        from ..pluginentries.handlerchannel import ChannelHandler
        handler = ChannelHandler.get(self.url)

        return handler.get_channel_url()

    def is_channel_page_url(self):
        from ..pluginentries.handlerchannel import ChannelHandler
        return ChannelHandler.get_supported(self.url)

    def fix_entries(self):
        entries = LinkDataModel.objects.filter(source=self.url)
        for entry in entries:
            entry.source_obj = self
            entry.save()


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

    def move_old_links_to_archive():
        from ..dateutils import DateUtils

        conf = Configuration.get_object().config_entry

        if conf.days_to_move_to_archive == 0:
            return

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)

        entries = LinkDataController.objects.filter(
            bookmarked=False, permanent=False, date_published__lt=days_before
        )

        for entry in entries:
            if entry.get_source_obj() is None:
                entry.move_to_archive()
            elif entry.get_source_obj().get_days_to_remove() == 0:
                entry.move_to_archive()

    def get_full_information(data):
        reader = EntryPageDataReader(data)
        return reader.get_full_information()

    def clear_old_entries():
        from ..dateutils import DateUtils

        sources = SourceDataController.objects.all()
        for source in sources:
            if not source.is_removeable():
                continue

            days = source.get_days_to_remove()
            if days > 0:
                days_before = DateUtils.get_days_before_dt(days)

                entries = LinkDataController.objects.filter(
                    source=source.url,
                    bookmarked=False,
                    permanent=False,
                    date_published__lt=days_before,
                )
                if entries.exists():
                    PersistentInfo.create(
                        "Removing old RSS data for source: {0} {1}".format(
                            source.url, source.title
                        )
                    )
                    entries.delete()

        config = Configuration.get_object().config_entry
        days = config.days_to_remove_links
        if days != 0:
            days_before = DateUtils.get_days_before_dt(days)

            entries = LinkDataController.objects.filter(
                bookmarked=False,
                permanent=False,
                date_published__lt=days_before,
            )
            if entries.exists():
                entries.delete()

            entries = ArchiveLinkDataController.objects.filter(
                bookmarked=False,
                permanent=False,
                date_published__lt=days_before,
            )
            if entries.exists():
                entries.delete()


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
                    "[{}]:Adding link: {}".format(LinkDatabase.name, link_data["link"])
                )

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

        new_link_data = dict(link_data)
        if "date_published" not in new_link_data:
            new_link_data["date_published"] = DateUtils.get_datetime_now_utc()

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

    def create_from_youtube(url, data):
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

        return LinkDataHyperController.add_new_link(link_data)

    def add_addition_link_data(link_data):
        try:
            config = Configuration.get_object().config_entry
            if config.auto_store_domain_info:
                domains = set()
                
                if "source" in link_data:
                    print("Adding 0 domain for: {}".format(link_data["source"]))
                    p = BasePage(link_data["source"])
                    domain = p.get_domain()
                    if domain == None or domain == "" or domain == "http://" or domain == "https://":
                        LinkDataHyperController.store_error_info(domain, "Invalid source domain")
                    domains.add(domain)

                p = BasePage(link_data["link"])
                domain = p.get_domain()
                print("Adding 1 domain for: {}".format(domain))
                domains.add(domain)
                if domain == None or domain == "" or domain == "http://" or domain == "https://":
                    LinkDataHyperController.store_error_info(domain, "Invalid link domain")

                parser = ContentLinkParser(link_data["link"], link_data["description"])
                description_links = parser.get_links()

                for link in description_links:
                    print("Adding 2 domain for: {}".format(link))
                    ppp = BasePage(link)
                    domain = ppp.get_domain()
                    if domain == None or domain == "" or domain == "http://" or domain == "https://":
                        text = "Invalid description line link:{} domain:{} description:{}".format(link, domain, link_data["description"])
                        LinkDataHyperController.store_error_info(domain, text)
                    else:
                        domains.add(domain)
                    
                for domain in domains:
                    if domain != None and domain != "" and domain != "http://" and domain != "https://":
                         Domains.add(domain)

            if config.auto_store_keyword_info:
                if "title" in link_data:
                    KeyWords.add_link_data(link_data)
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

    def store_error_info(url, info):
        lines = traceback.format_stack()
        line_text = ""
        for line in lines:
            line_text += line

        PersistentInfo.error(
            "Domain{};{};Lines:{}".format(
                url, info, line_text
            )
        )

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
        else:
            try:
                entry.delete()
            except Exception as e:
                error_text = traceback.format_exc()

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
            Domains.add(obj.link)

    def get_clean_description(link_data):
        import re

        # as per recommendation from @freylis, compile once only
        CLEANR = re.compile("<.*?>")

        cleantext = re.sub(CLEANR, "", link_data["description"])
        return cleantext
        # from bs4 import BeautifulSoup
        # cleantext = BeautifulSoup(link_data["description"], "lxml").text
        # return cleantext


class LinkCommentDataController(LinkCommentDataModel):
    class Meta:
        proxy = True

    def can_user_add_comment(link_id, user_name):
        now = datetime.now()
        time_start = now - timedelta(days=1)
        time_stop = now

        link = LinkDataModel.objects.get(id=link_id)

        criterion0 = Q(author=user_name, link_obj=link)
        criterion1 = Q(date_published__range=[time_start, time_stop])
        criterion2 = Q(date_edited__range=[time_start, time_stop])

        comments = LinkCommentDataModel.objects.filter(
            criterion0 & (criterion1 | criterion2)
        )

        conf = Configuration.get_object().config_entry

        if comments.count() > conf.number_of_comments_per_day:
            return False

        return True

    def save_comment(data):
        entry = LinkDataController.objects.get(id=data["link_id"])

        LinkCommentDataModel.objects.create(
            author=data["author"],
            comment=data["comment"],
            date_published=data["date_published"],
            link_obj=entry,
        )


class DomainsController(Domains):
    """
    TODO copy methods from model
    """
    class Meta:
        proxy = True


class BackgroundJobController(BackgroundJob):
    class Meta:
        proxy = True

    def truncate():
        BackgroundJob.objects.all().delete()

    def truncate_invalid_jobs():
        job_choices = BackgroundJob.JOB_CHOICES
        valid_jobs_choices = []
        for job_choice in job_choices:
            valid_jobs_choices.append(job_choice[0])

        jobs = BackgroundJob.objects.all()
        for job in jobs:
            if job.job not in valid_jobs_choices:
                print("Clearing job {}".format(job.job))
                job.delete()

    def get_number_of_jobs(job_name=None):
        if job_name is None:
            return BackgroundJob.objects.all().count()
        return BackgroundJob.objects.filter(job=job_name).count()

    def create_single_job(job_name, subject="", args=""):
        try:
            items = BackgroundJob.objects.filter(job=job_name, subject=subject)
            if items.count() == 0:
                BackgroundJob.objects.create(
                    job=job_name,
                    task=None,
                    subject=subject,
                    args=args,
                )
                return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: {}: {} {}".format(job_name, str(e), error_text)
            )

    def download_rss(source, force=False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PROCESS_SOURCE, source.url
        )

    def download_music(item):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, item.link
        )

    def download_video(item):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, item.link
        )

    def update_entry_data(url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_UPDATE_DATA, url
        )

    def link_add(url, source):
        existing = LinkDataModel.objects.filter(link=url)
        if existing.count() > 0:
            return False

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_ADD, url, str(source.id)
        )

    def write_daily_data_range(date_start=date.today(), date_stop=date.today()):
        try:
            if date_stop < date_start:
                PersistentInfo.error(
                    "Yearly generation: Incorrect configuration of dates start:{} stop:{}".format(
                        date_start, date_stop
                    )
                )
                return False

            sent = False
            current_date = date_start
            while current_date <= date_stop:
                str_date = current_date.isoformat()
                current_date += timedelta(days=1)

                BackgroundJobController.write_daily_data(str_date)
                sent = True

            return sent
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Daily data: {} {}".format(str(e), error_text)
            )

    def write_daily_data(input_date):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_DAILY_DATA, input_date
        )

    def write_daily_data_str(start="2022-01-01", stop="2022-12-31"):
        try:
            date_start = datetime.strptime(start, "%Y-%m-%d").date()
            date_stop = datetime.strptime(stop, "%Y-%m-%d").date()

            BackgroundJobController.write_daily_data_range(date_start, date_stop)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Daily data: {} {}".format(str(e), error_text)
            )

    def write_tag_data(tag):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_TOPIC_DATA, tag
        )

    def write_bookmarks():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_BOOKMARKS
        )

    def import_daily_data():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_DAILY_DATA
        )

    def import_bookmarks():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_BOOKMARKS
        )

    def import_sources():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_SOURCES
        )

    def link_save(link_url):
        try:
            archive_items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_LINK_SAVE
            )
            if archive_items.count() < 100:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_LINK_SAVE,
                    task=None,
                    subject=link_url,
                    args="",
                )
                return True
            else:
                for key, obj in enumerate(archive_items):
                    if key > 100:
                        obj.delete()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Link archive: {} {}".format(str(e), error_text)
            )

    def link_download(link_url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD, link_url
        )

    def push_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_TO_REPO, input_date
        )

    def push_daily_data_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO, input_date
        )

    def push_year_data_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_YEAR_DATA_TO_REPO, input_date
        )

    def push_notime_data_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_NOTIME_DATA_TO_REPO, input_date
        )

    def make_cleanup():
        return BackgroundJobController.create_single_job(BackgroundJob.JOB_CLEANUP)

    def check_domains():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CHECK_DOMAINS
        )

    def import_from_instance(link):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_INSTANCE, link
        )

