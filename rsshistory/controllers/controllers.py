from datetime import datetime, date, timedelta
import os
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
    DomainCategories,
    DomainSubCategories,
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
            DomainsController.add(source_data_map["url"])

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
                SourceOperationalData.objects.create(
                    url=self.url,
                    date_fetched=date_fetched,
                    import_seconds=import_seconds,
                    number_of_entries=number_of_entries,
                    page_hash=hash_value,
                    source_obj=self,
                )
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
        p = HtmlPage(data["url"])
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

    def move_old_links_to_archive(limit=0):
        """
        from ..dateutils import DateUtils

        conf = Configuration.get_object().config_entry

        if conf.days_to_move_to_archive == 0:
            return

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)

        index = 0
        while True:
            entries = LinkDataController.objects.filter(
                bookmarked=False, permanent=False, date_published__lt=days_before
            )

            if not entries.exists():
                break

            entry = entries[0]

            print(
                "[{}]:Moving link to archive: {}".format(LinkDatabase.name, entry.link)
            )

            LinkDataController.move_to_archive(entry)
            index += 1

            if limit and index > limit:
                break
        """

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
                PersistentInfo.error("Cannot move to archive {}".format(error_text))

    def get_full_information(data):
        reader = EntryPageDataReader(data)
        return reader.get_full_information()

    def clear_old_entries(limit=0):
        """
        This function can clear many many links, so we do not perform entries.delete.
        We do it one-by-one.
        It also could have been by using django batch jobs.
        These loops are dangerous. We could be finding again some entries,
         if we added any conditions.
        """
        """
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

                while True:
                    entries = LinkDataController.objects.filter(
                        source=source.url,
                        bookmarked=False,
                        permanent=False,
                        date_published__lt=days_before,
                    )
                    if not entries.exists():
                        break

                    entry = entries[0]

                    print(
                            "[{}] Removing link:{}".format(
                            LinkDatabase.name, entry.link
                        )
                    )

                    entry.delete()
                    index += 1
                    if limit and index > limit:
                        return

        days = config_days
        if days != 0:
            days_before = DateUtils.get_days_before_dt(days)

            while True:
                entries = LinkDataController.objects.filter(
                    bookmarked=False,
                    permanent=False,
                    date_published__lt=days_before,
                )

                if not entries.exists():
                    break

                entry = entires[0]

                print(
                        "[{}] Removing link:{}".format(
                        LinkDatabase.name, entry.link
                    )
                )

                entry.delete()
                index += 1

                if limit and index > limit:
                    return

            while True:
                entries = ArchiveLinkDataController.objects.filter(
                    bookmarked=False,
                    permanent=False,
                    date_published__lt=days_before,
                )

                if not entries.exists():
                    break

                entry = entires[0]

                print(
                        "[{}] Removing link:{}".format(
                        LinkDatabase.name, entry.link
                    )
                )

                entry.delete()
                index += 1

                if limit and index > limit:
                    return
        """
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
                if entries.exists():
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

                # TODO - add source domain when source is added

                # if "source" in link_data:
                #    print("Adding 0 domain for: {}".format(link_data["source"]))
                #    p = BasePage(link_data["source"])
                #    domain = p.get_domain()
                #    if (
                #        domain == None
                #        or domain == ""
                #        or domain == "http://"
                #        or domain == "https://"
                #    ):
                #        LinkDataHyperController.store_error_info(
                #            domain, "Invalid source domain"
                #        )
                #    domains.add(domain)

                p = BasePage(link_data["link"])
                domain = p.get_domain()
                domains.add(domain)
                if (
                    domain == None
                    or domain == ""
                    or domain == "http://"
                    or domain == "https://"
                ):
                    LinkDataHyperController.store_error_info(
                        domain, "Invalid link domain"
                    )

                parser = ContentLinkParser(link_data["link"], link_data["description"])
                description_links = parser.get_links()

                for link in description_links:
                    ppp = BasePage(link)
                    domain = ppp.get_domain()
                    if (
                        domain == None
                        or domain == ""
                        or domain == "http://"
                        or domain == "https://"
                    ):
                        text = "Invalid description line link:{} domain:{} description:{}".format(
                            link, domain, link_data["description"]
                        )
                        LinkDataHyperController.store_error_info(domain, text)
                    else:
                        domains.add(domain)

                for domain in domains:
                    if (
                        domain != None
                        and domain != ""
                        and domain != "http://"
                        and domain != "https://"
                    ):
                        DomainsController.add(domain)

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
            DomainsController.add(obj.link)

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

    def create_missing_domains():
        if not Configuration.get_object().config_entry.auto_store_domain_info:
            return

        entries = LinkDataController.objects.filter(permanent=True)
        for entry in entries:
            if not DomainsController.is_domain_object(entry):
                p = BasePage(entry.link)
                if p.is_domain():
                    print("Create missing domains entry:{} - domain".format(entry.link))
                    domains = Domains.objects.filter(domain=p.get_domain())
                    if domains.count() == 0:
                        print(
                            "Create missing domains entry:{} - missing domain".format(
                                entry.link
                            )
                        )
                        DomainsController.add(p.get_domain())
                    else:
                        print(
                            "Create missing domains entry:{} - missing domain link".format(
                                entry.link
                            )
                        )
                        domain = domains[0]
                        domain.link_obj = entry.link

    def is_domain_object(entry):
        if not hasattr(entry, "domain_obj"):
            return False

        return entry.domain_obj

    def add(url):
        """
        Public API
        """
        wh = url.find(":")
        if wh > 8:
            url = url[:wh]

        if url.strip() == "":
            print("Provided invalid URL, empty")
            return

        if url.find("http") == -1:
            url = "https://" + url

        domain_text = DomainsController.get_domain_url(url)
        if (
            not domain_text
            or domain_text == ""
            or domain_text == "https://"
            or domain_text == "http://"
            or domain_text == "https"
            or domain_text == "http"
        ):
            PersistentInfo.create(
                "Not a domain text:{}, url:{}".format(domain_text, url)
            )
            return

        return DomainsController.create_or_update_domain(domain_text)

    def get_domain_url(input_url):
        p = BasePage(input_url)
        domain_text = p.get_domain_only()
        return domain_text

    def get_domain_full_url(self, protocol=None):
        if protocol is None:
            return self.protocol + "://" + self.domain
        else:
            return protocol + "://" + self.domain

    def get_absolute_url(self):
        return reverse(
            "{}:domain-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

    def create_or_update_domain(domain_only_text):
        print(
            "[{}] Creating, or updating domain:{}".format(
                LinkDatabase.name, domain_only_text
            )
        )
        objs = Domains.objects.filter(domain=domain_only_text)

        obj = None
        if objs.count() == 0:
            props = DomainsController.get_link_properties(domain_only_text)
            if props:
                obj = DomainsController.create_object(domain_only_text, props)
        else:
            obj = objs[0]

        if obj:
            return obj.id

    def create_object(domain_only_text, props):
        import tldextract

        if props:
            entry = DomainsController.add_domain_entry(props)
            if entry is None:
                PersistentInfo.error(
                    "Entry is None, cannot add domain {}".format(domain_only_text)
                )
                return

            extract = tldextract.TLDExtract()
            domain_data = extract(domain_only_text)

            tld = os.path.splitext(domain_only_text)[1][1:]

            old_entries = Domains.objects.filter(link_obj=entry)
            if old_entries.count() > 0:
                ob = old_entries[0]
                ob.domain = domain_only_text
                ob.main = domain_data.domain
                ob.subdomain = domain_data.subdomain
                ob.suffix = domain_data.suffix
                ob.tld = tld
                ob.save()

            else:
                ob = DomainsController.objects.create(
                    domain=domain_only_text,
                    main=domain_data.domain,
                    subdomain=domain_data.subdomain,
                    suffix=domain_data.suffix,
                    tld=tld,
                    link_obj=entry,
                )

                ob.update_complementary_data(True)
                ob.check_and_create_source(props)

            return ob

    def get_link_properties(domain_only):
        if domain_only.find("http") >= 0:
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            PersistentInfo.create(
                "Cannot obtain properties, expecting only domain:{}\n{}".format(
                    domain_only, line_text
                )
            )
            return

        link = "https://" + domain_only

        p = HtmlPage(link)
        if p.get_contents() is None:
            link = "http://" + domain_only
            p = HtmlPage(link)
            if p.get_contents() is None:
                return
            return p.get_properties_map()

        return p.get_properties_map()

    def get_page_properties(self):
        # if self.link_obj is not None:
        #    return

        link = DomainsController.get_domain_url(self.get_domain_full_url())
        return DomainsController.get_link_properties(link)

    def update_object(self, force=False):
        if self.is_domain_set() == False:
            self.update_domain()

        self.update_complementary_data(force)

        if self.link_obj == None:
            props = self.get_page_properties()
            if props:
                self.check_and_create_source(props)
            else:
                self.dead = True
                self.save()

    def add_domain_entry(props):
        link_props = {}
        link_props["link"] = props["link"]
        link_props["title"] = props["title"]
        link_props["description"] = props["description"]
        link_props["page_rating_contents"] = props["page_rating"]
        link_props["page_rating"] = props["page_rating"]
        link_props["language"] = props["language"]

        entry = LinkDataHyperController.add_new_link(link_props)
        return entry

    def check_and_create_source(self, props):
        rss_url = props["rss_url"]
        if not rss_url:
            return

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        if SourceDataModel.objects.filter(url=rss_url).count() > 0:
            return

        if self.link_obj and self.link_obj.dead:
            return

        conf = Configuration.get_object().config_entry

        if not conf.auto_store_sources:
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

    def get_domain_ext(self, domain_only_text):
        tld = os.path.splitext(domain_only_text)[1][1:]
        wh = tld.find(":")
        if wh >= 0:
            tld = tld[:wh]
        return tld

    def is_domain_set(self):
        return (
            self.suffix is not None
            and self.tld is not None
            and self.suffix != ""
            and self.tld != ""
        )

    def is_page_info_set(self):
        return (
            self.title is not None
            and self.description is not None
            and self.language is not None
        )

    def is_update_time(self):
        from ..dateutils import DateUtils

        days = DateUtils.get_day_diff(self.date_update_last)
        # TODO make this configurable
        return days > Domains.get_update_days_limit()

    def update_domain(self):
        import tldextract
        from ..dateutils import DateUtils

        changed = False

        if self.suffix is None or self.suffix == "":
            extract = tldextract.TLDExtract()
            domain_data = extract(self.domain)

            self.main = domain_data.domain
            self.subdomain = domain_data.subdomain
            self.suffix = domain_data.suffix
            changed = True

        if self.tld is None or self.tld == "":
            self.tld = self.get_domain_ext(self.domain)
            changed = True

        if changed:
            print(
                "domain:{} subdomain:{} suffix:{} tld:{} title:{}".format(
                    self.main, self.subdomain, self.suffix, self.tld, self.title
                )
            )

            self.save()

            self.update_complementary_data()

        else:
            print("domain:{} Nothing has changed".format(self.domain))

    def update_page_info(self):
        # if self.title is not None and self.description is not None and self.dead == False and not force:
        #    print("Domain: not fixing title/description {} {} {}".format(self.domain, self.suffix, self.tld))
        #    return False
        if self.link_obj is not None:
            return

        print("Fixing title {}".format(self.domain))

        from ..dateutils import DateUtils

        date_before_limit = DateUtils.get_days_before_dt(
            DomainsController.get_update_days_limit()
        )
        if self.date_update_last >= date_before_limit:
            return

        changed = False

        p = HtmlPage(self.get_domain_full_url())

        new_title = p.get_title()
        new_description = p.get_description_safe()[:998]
        new_language = p.get_language()
        protocol = self.protocol

        if new_title is None:
            print("{} Trying with http".format(self.domain))
            p = HtmlPage(self.get_domain_full_url("http"))
            new_title = p.get_title()
            new_description = p.get_description_safe()[:998]
            new_language = p.get_language()

        print("Page status:{}".format(p.is_status_ok()))

        self.status_code = p.status_code

        if p.is_valid() == False:
            self.dead = True
            self.date_update_last = DateUtils.get_datetime_now_utc()
            self.save()
            return

        if self.dead and p.is_status_ok():
            self.dead = False
            changed = True

        print("New title:{}".format(new_title))
        print("New description:{}".format(new_description))

        if new_title is not None:
            self.title = new_title
            changed = True
        if new_description is not None:
            self.description = new_description
            changed = True
        if new_language is not None:
            self.language = new_language
            changed = True
        if new_title is not None and new_description is None:
            self.description = None
            changed = True

        if changed:
            self.date_update_last = DateUtils.get_datetime_now_utc()
            self.protocol = protocol
            self.save()

    def update_all(domains=None):
        if domains is None:
            from ..dateutils import DateUtils

            date_before_limit = DateUtils.get_days_before_dt(
                Domains.get_update_days_limit()
            )

            domains = Domains.objects.filter(
                date_update_last__lt=date_before_limit, dead=False, link_obj=None
            )
            # domains = Domains.objects.filter(dead = True) #, description__isnull = True)

        for domain in domains:
            print("Fixing:{}".format(domain.domain))
            try:
                domain.update_object()
            except Exception as e:
                print(str(e))
            print("Fixing:{} done".format(domain.domain))

    def remove(self):
        link = self.get_domain_full_url()
        entry = LinkDataHyperController.get_link_object(link)
        if entry:
            entry.delete()

        self.delete()

    def get_map(self):
        result = {
            "protocol": self.protocol,
            "domain": self.domain,
            "main": self.main,
            "subdomain": self.subdomain,
            "suffix": self.suffix,
            "tld": self.tld,
            "category": self.category,
            "subcategory": self.subcategory,
            "dead": self.dead,
            "date_created": self.date_created.isoformat(),
            "date_update_last": self.date_update_last.isoformat(),
        }
        return result

    def get_query_names():
        result = [
            "protocol",
            "domain",
            "main",
            "subdomain",
            "suffix",
            "tld",
            "category",
            "subcategory",
            "dead",
            "date_created",
            "date_update_last",
        ]
        return result

    def reset_dynamic_data():
        objs = DomainCategories.objects.all()
        objs.delete()
        objs = DomainSubCategories.objects.all()
        objs.delete()

        domains = Domains.objects.all()
        for domain in domains:
            DomainCategories.add(domain.category)
            DomainSubCategories.add(domain.category, domain.subcategory)

    def get_description_safe(self):
        if self.description:
            if len(self.description) > 100:
                return self.description[:100] + "..."
            else:
                return self.description
        else:
            return ""


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
