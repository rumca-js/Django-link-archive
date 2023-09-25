from datetime import datetime, date, timedelta
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from .models import (
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
from .webtools import Page

from .apps import LinkDatabase


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

    def add(source_data_map):
        sources = SourceDataController.objects.filter(url = source_data_map["url"])
        if sources.count() > 0:
            return None

        # TODO add domain when adding new source
        source = SourceDataController.objects.create(**source_data_map)

        if ConfigurationEntry.get().store_domain_info:
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
        except:
            pass

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
        from datetime import timedelta
        from .dateutils import DateUtils

        if self.on_hold:
            return False

        start_time = DateUtils.get_datetime_now_utc()

        date_fetched = self.get_date_fetched()
        if date_fetched:
            time_since_update = start_time - date_fetched
            # mins = time_since_update / timedelta(minutes=1)
            secs = time_since_update / timedelta(seconds=1)

            # if mins >= 30:
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
        objs = self.dynamic_data.all()
        if objs.count() == 0:
            return None
        return objs[0]

    def get_date_fetched(self):
        obj = self.get_op_data()
        if obj:
            return obj.date_fetched

    def get_import_seconds(self):
        obj = self.get_op_data()
        if obj:
            return obj.import_seconds

    def get_number_of_entries(self):
        obj = self.get_op_data()
        if obj:
            return obj.number_of_entries

    def set_operational_info(self, date_fetched, number_of_entries, import_seconds):
        obj = self.get_op_data()
        if obj:
            obj.date_fetched = date_fetched
            obj.import_seconds = import_seconds
            obj.number_of_entries = number_of_entries
            obj.save()
        else:
            objs = SourceOperationalData.objects.filter(url=self.url, source_obj=None)
            if objs.count() >= 0:
                objs.delete()

            op = SourceOperationalData(
                url=self.url,
                date_fetched=date_fetched,
                import_seconds=import_seconds,
                number_of_entries=number_of_entries,
                source_obj=self,
            )
            op.save()

    def get_favicon(self):
        if self.favicon:
            return self.favicon

        from .webtools import Page

        page = Page(self.url)
        domain = page.get_domain()
        return domain + "/favicon.ico"

    def get_domain(self):
        from .webtools import Page

        page = Page(self.url)
        return page.get_domain()

    def get_domain_only(self):
        from .webtools import Page

        page = Page(self.url)
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

    def is_page_rss(page, data):
        try:
            import feedparser
            feed = feedparser.parse(data["url"])
            return True
        except Exception as e:
            return False

        #wh1 = page.get_contents().find("<rss version=")
        #wh2 = page.get_contents().find("<feed")
        #if wh1 >= 0 or wh2 >= 0:
        #    return True

    def get_full_information(data):
        p = Page(data["url"])
        # TODO if passed url is youtube video, obtain information, obtain channel feed url

        if SourceDataController.is_page_rss(p, data):
            return SourceDataController.get_info_from_rss(data["url"])
        elif p.get_rss_url():
            return SourceDataController.get_info_from_rss(p.get_rss_url())
        else:
            return SourceDataController.get_info_from_page(data["url"], p)

    def get_info_from_rss(url):
        import feedparser

        feed = feedparser.parse(url)
        data = {}
        data["url"] = url
        data["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
        if "title" in feed.feed:
            data["title"] = feed.feed.title
        if "subtitle" in feed.feed:
            data["description"] = feed.feed.subtitle
        if "language" in feed.feed:
            data["language"] = feed.feed.language
        if "image" in feed.feed:
            if 'href' in feed.feed.image:
                data["favicon"] = feed.feed.image['href']
            else:
                data["favicon"] = feed.feed.image
        return data

    def get_info_from_page(url, p):
        data = {}
        data["url"] = url
        data["source_type"] = SourceDataModel.SOURCE_TYPE_PARSE
        data["language"] = p.get_language()
        data["title"] = p.get_title()
        data["description"] = p.get_title()
        return data

    def get_channel_page_url(self):
        from .pluginsources.youtubesourcehandler import YouTubeSourceHandler

        return YouTubeSourceHandler.input2url(self.url)


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
        from .dateutils import DateUtils

        conf = ConfigurationEntry.get()

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)

        entries = LinkDataController.objects.filter(
            bookmarked=False, date_published__lt=days_before
        )

        for entry in entries:
            if entry.get_source_obj() is None:
                entry.move_to_archive()
            elif entry.get_source_obj().get_days_to_remove() == 0:
                entry.move_to_archive()

    def clear_old_entries():
        from .dateutils import DateUtils

        sources = SourceDataController.objects.all()
        for source in sources:
            if not source.is_removeable():
                continue

            days = source.get_days_to_remove()
            if days > 0:
                current_time = DateUtils.get_datetime_now_utc()
                days_before = current_time - timedelta(days=days)

                entries = LinkDataController.objects.filter(
                    source=source.url, bookmarked=False, date_published__lt=days_before
                )
                if entries.exists():
                    PersistentInfo.create(
                        "Removing old RSS data for source: {0} {1}".format(
                            source.url, source.title
                        )
                    )
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
    def add_new_link(link_data):
        if "source_obj" not in link_data:
            source_obj = None
            sources = SourceDataController.objects.filter(url=link_data["source"])
            if sources.exists():
                source_obj = sources[0]

            link_data["source_obj"] = source_obj

        is_archive = BaseLinkDataController.is_archive_by_date(link_data["date_published"])
        if not is_archive or link_data["bookmarked"]:
            objs = LinkDataModel.objects.filter(link=link_data["link"])
            if not objs.exists():
                o = LinkDataModel(**link_data)
                o.save()
                # if link exists - do not change data
                LinkDataHyperController.add_new_link_data(link_data)
                return True

        elif is_archive:
            objs = ArchiveLinkDataModel.objects.filter(link=link_data["link"])
            if not objs.exists():
                o = ArchiveLinkDataModel(**link_data)
                o.save()
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
        from .pluginentries.youtubelinkhandler import YouTubeLinkHandler

        objs = LinkDataController.objects.filter(link=url)
        if objs.count() != 0:
            return False

        h = YouTubeLinkHandler(url)
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

    def add_new_link_data(link_data):
        try:
            if ConfigurationEntry.get().store_domain_info:
                p = Page(link_data["source"])
                domain = p.get_domain_only()
                Domains.add(domain)

                p = Page(link_data["link"])
                domain = p.get_domain_only()
                Domains.add(domain)

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

    def get_link_object(link, date=None):
        conf = ConfigurationEntry.get()

        if date is None:
            obj = LinkDataController.objects.filter(link=link)
            if obj.count() > 0:
                return obj[0]
            obj = ArchiveLinkDataController.objects.filter(link=link)
            if obj.count() > 0:
                return obj[0]

        current_time = DateUtils.get_datetime_now_utc()
        date_before = current_time - date
        if date_before.days > conf.days_to_move_to_archive:
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
        from .dateutils import DateUtils

        days_diff = DateUtils.get_day_diff(entry.date_published)

        conf = ConfigurationEntry.get()

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
        CLEANR = re.compile('<.*?>')

        cleantext = re.sub(CLEANR, '', link_data["description"])
        return cleantext
        #from bs4 import BeautifulSoup
        #cleantext = BeautifulSoup(link_data["description"], "lxml").text
        #return cleantext


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

        conf = ConfigurationEntry.get()

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

    def get_number_of_jobs(job_name = None):
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

    def youtube_details(url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DETAILS, url
        )

    def link_add(url, source):
        existing = LinkDataModel.objects.filter(link=url)
        if existing.count() > 0:
            return False

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_ADD, url, str(source.id)
        )

    def write_daily_data_range(date_start=date.today(), date_stop=date.today()):
        from datetime import timedelta

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

    def make_cleanup():
        return BackgroundJobController.create_single_job(BackgroundJob.JOB_CLEANUP)

    def check_domains():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CHECK_DOMAINS
        )
