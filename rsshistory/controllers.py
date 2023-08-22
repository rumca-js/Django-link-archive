from datetime import datetime, date, timedelta
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from .models.linkmodels import (
    BaseLinkDataModel,
    BaseLinkDataController,
    LinkDataModel,
    ArchiveLinkDataModel,
)
from .models import (
    BackgroundJob,
    PersistentInfo,
    ConfigurationEntry,
    SourceDataModel,
    SourceOperationalData,
    LinkCommentDataModel,
    LinkTagsDataModel,
    LinkVoteDataModel,
    Domains,
    )
from .webtools import Page

from .apps import LinkDatabase


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

    def add(source_data_map):
        # TODO add domain when adding new source
        SourceDataModel.objects.create(**source_data_map)
        
        if ConfigurationEntry.get().store_domain_info:
            Domains.add(source_data_map["url"])

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
        return "{} {}".format(self.category, self.subcategory)

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
        if len(objs) == 0:
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
            if len(objs) >= 0:
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
        p = Page(data["url"])
        # TODO if passed url is youtube video, obtain information, obtain channel feed url

        wh1 = p.get_contents().find("<rss version=")
        wh2 = p.get_contents().find("<feed")
        if wh1 >= 0 or wh2 >= 0:
            return SourceDataController.get_info_from_rss(data["url"])
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

    def move_old_links_to_archive():
        from .dateutils import DateUtils

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(
            days=BaseLinkDataController.get_archive_days_limit()
        )

        entries = LinkDataController.objects.filter(
            persistent=False, date_published__lt=days_before
        )

        for entry in entries:
            if entry.get_source_obj() is None:
                entry.move_to_archive()
            elif entry.get_source_obj().get_days_to_remove() == 0:
                entry.move_to_archive()

    def clear_old_entries():
        sources = SourceDataController.objects.all()
        for source in sources:
            if not source.is_removeable():
                continue

            days = source.get_days_to_remove()
            if days > 0:
                current_time = DateUtils.get_datetime_now_utc()
                days_before = current_time - timedelta(days=days)

                entries = LinkDataController.objects.filter(
                    source=source.url, persistent=False, date_published__lt=days_before
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


class LinkDataHyperController(object):

    def add_new_link(link_data):
 
        if "source_obj" not in link_data:
            source_obj = None
            sources = SourceDataController.objects.filter(url=link_data["source"])
            if sources.exists():
                source_obj = sources[0]

            link_data["source_obj"] = source_obj

        objs = LinkDataModel.objects.filter(link=link_data["link"])
        if not objs.exists():
            o = LinkDataModel(**link_data)
        try:
            o.save()

            p = Page(link_data["source"])
            domain = p.get_domain_only()
            Domains.add(domain)

            p = Page(link_data["link"])
            domain = p.get_domain_only()
            Domains.add(domain)

            return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "Could not {} entry: Source:{} {}; Entry:{} {}; Exc:{}\n{}".format(
                    method,
                    source.url,
                    source.title,
                    link_data["link"],
                    link_data["title"],
                    str(e),
                    error_text,
                )
            )
        return False

    def get_link_object(link, date=None):
        if date is None:
            obj = LinkDataController.objects.filter(link=link)
            if len(obj) > 0:
                return obj[0]
            obj = ArchiveLinkDataController.objects.filter(link=link)
            if len(obj) > 0:
                return obj[0]

        current_time = DateUtils.get_datetime_now_utc()
        date_before = current_time - date
        if date_before.days > self.get_archive_days_limit():
            obj = ArchiveLinkDataController.objects.filter(link=link)
            if len(obj) > 0:
                return obj[0]
        else:
            obj = LinkDataController.objects.filter(link=link)
            if len(obj) > 0:
                return obj[0]

    def make_persistent(self, request, entry):
        if entry.is_archive():
            LinkDataHyperController.move_from_archive(entry)

        entry.make_persistent(request.user.username)
        return True

    def make_not_persistent(self, request, entry):
        entry.make_not_persistent(request.user.username)

        days_diff = DateUtils.get_day_diff(entry.date_published)

        if days_diff > BaseLinkDataController.get_archive_days_limit():
            LinkDataHyperController.move_to_archive(entry)

        return True

    def move_to_archive(entry):
        objs = ArchiveLinkDataModel.objects.filter(link=entry.link)
        if len(objs) == 0:
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
        if len(objs) == 0:
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
        objs = LinkDataModel.objects.filter(persistent=True)
        for obj in objs:
            Domains.add(obj.link)


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

        if len(comments) > 0:
            return False

        return True


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

    def get_number_of_jobs(job_type):
        return len(BackgroundJob.objects.filter(job=job_type))

    def download_rss(source, force=False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        if (
            len(
                BackgroundJob.objects.filter(
                    job=BackgroundJob.JOB_PROCESS_SOURCE, subject=source.url
                )
            )
            == 0
        ):
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_PROCESS_SOURCE,
                task=None,
                subject=source.url,
                args="",
            )

        return True

    def download_music(item):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC,
            task=None,
            subject=item.link,
            args="",
        )
        return True

    def download_video(item):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO,
            task=None,
            subject=item.link,
            args="",
        )
        return True

    def youtube_details(url):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DETAILS, task=None, subject=url, args=""
        )
        return True

    def link_add(url, source):
        existing = LinkDataModel.objects.filter(link=url)
        if len(existing) > 0:
            return False

        if (
            len(
                BackgroundJob.objects.filter(
                    job=BackgroundJob.JOB_LINK_ADD, subject=url
                )
            )
            == 0
        ):
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_LINK_ADD,
                task=None,
                subject=url,
                args=str(source.id),
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

                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_WRITE_DAILY_DATA,
                    task=None,
                    subject=str_date,
                    args="",
                )
                sent = True

            return sent
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Daily data: {} {}".format(str(e), error_text)
            )

    def write_daily_data(input_date):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_WRITE_DAILY_DATA,
            task=None,
            subject=input_date,
            args="",
        )
        return True

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
        try:
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_WRITE_TOPIC_DATA, task=None, subject=tag, args=""
            )
            return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Tag data: {} {}".format(str(e), error_text)
            )

    def write_bookmarks():
        try:
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_WRITE_BOOKMARKS, task=None, subject="", args=""
            )
            return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Write bookmarks: {} {}".format(str(e), error_text)
            )

    def import_daily_data():
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_IMPORT_DAILY_DATA,
            task=None,
            subject="",
            args="",
        )
        return True

    def import_bookmarks():
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_IMPORT_BOOKMARKS,
            task=None,
            subject="",
            args="",
        )
        return True

    def import_sources():
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_IMPORT_SOURCES,
            task=None,
            subject="",
            args="",
        )
        return True

    def link_archive(link_url):
        try:
            archive_items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_LINK_ARCHIVE
            )
            if len(archive_items) < 100:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_LINK_ARCHIVE,
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
        try:
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_LINK_DOWNLOAD,
                task=None,
                subject=link_url,
                args="",
            )
            return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Link download: {} {}".format(str(e), error_text)
            )

    def push_to_repo(input_date=""):
        try:
            items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_PUSH_TO_REPO, subject=""
            )
            if len(items) == 0:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_PUSH_TO_REPO,
                    task=None,
                    subject=input_date,
                    args="",
                )
                return True
            elif len(items) > 1:
                for item in items:
                    item.delete()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Link download: {} {}".format(str(e), error_text)
            )

    def push_daily_data_to_repo(input_date=""):
        try:
            items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO, subject=""
            )
            if len(items) == 0:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO,
                    task=None,
                    subject=input_date,
                    args="",
                )
                return True
            elif len(items) > 1:
                for item in items:
                    item.delete()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Link download: {} {}".format(str(e), error_text)
            )
