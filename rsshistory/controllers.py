from datetime import datetime, date, timedelta
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from .models import (
    LinkDataModel,
    SourceDataModel,
    ArchiveLinkDataModel,
    BackgroundJob,
    PersistentInfo,
    SourceOperationalData,
)
from .models import LinkCommentDataModel, LinkTagsDataModel, LinkVoteDataModel
from .webtools import Page

from .apps import LinkDatabase


class SourceDataController(SourceDataModel):
    class Meta:
        proxy = True

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

    def get_link_object(link, date = None):
        if date is None:
            obj = LinkDataModel.objects.filter(link = link)
            if len(obj) > 0:
                return obj[0]
            obj = ArchiveLinkDataModel.objects.filter(link = link)
            if len(obj) > 0:
                return obj[0]

        current_time = DateUtils.get_datetime_now_utc()
        date_before = current_time - date
        if date_before.days > self.get_archive_days_limit():
            obj = ArchiveLinkDataModel.objects.filter(link = link)
            if len(obj) > 0:
                return obj[0]
        else:
            obj = LinkDataModel.objects.filter(link = link)
            if len(obj) > 0:
                return obj[0]

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse("{}:entry-detail".format(LinkDatabase.name), args=[str(self.id)])

    def get_source_name(self):
        if self.get_source_obj():
            return self.get_source_obj().title
        else:
            return self.source

    def get_link_dead_text(self):
        return "______"

    def get_title(self):
        if self.dead:
            return self.get_link_dead_text()
        return self.title

    def get_long_description(self):
        if self.dead:
            return self.get_link_dead_text()
        return "{} {}".format(self.date_published, self.get_source_name())

    def has_tags(self):
        return len(self.tags.all()) > 0

    def get_full_description(self):
        if self.dead:
            return self.get_link_dead_text()
        string = "{} {}".format(self.date_published, self.get_source_name())
        tags = self.get_tag_string()
        if tags:
            string += " Tags:{}".format(tags)
        if self.user:
            string += " User:{}".format(self.user)

        return string

    def get_tag_string(self):
        return LinkTagsDataModel.join_elements(self.tags.all())

    def get_vote(self):
        votes = self.votes.all()
        if len(votes) == 0:
            return 0

        sum_num = None
        for vote in votes:
            if sum_num == None:
                sum_num = vote.vote
            else:
                sum_num += vote.vote

        return sum_num / len(votes)

    def get_tag_map(self):
        # TODO should it be done by for tag in self.tags: tag.get_map()?
        result = []
        tags = self.tags.all()
        for tag in tags:
            result.append(tag.tag)
        return result

    def get_comment_vec(self):
        # TODO
        return []

    def update_language(self):
        if self.get_source_obj():
            self.language = self.get_source_obj().language
            self.save()
        else:
            from .webtools import Page

            page = Page(self.link)
            if page.is_valid():
                language = page.get_language()
                if language != None:
                    self.language = language
                    self.save()

    def get_favicon(self):
        if self.get_source_obj():
            return self.get_source_obj().get_favicon()

        from .webtools import Page

        page = Page(self.link)
        domain = page.get_domain()
        return domain + "/favicon.ico"

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail

        return self.get_favicon()

    def get_export_names():
        return [
            "source",
            "title",
            "description",
            "link",
            "date_published",
            "persistent",
            "dead",
            "artist",
            "album",
            "user",
            "language",
            "thumbnail",
        ]

    def get_all_export_names():
        return [
            "source",
            "title",
            "description",
            "link",
            "date_published",
            "persistent",
            "dead",
            "artist",
            "album",
            "user",
            "language",
            "thumbnail",
            "tags",
            "comments",
            "vote",
        ]

    def get_map(self):
        output_data = {}

        export_names = LinkDataController.get_export_names()
        for export_name in export_names:
            val = getattr(self, export_name)
            if export_name.find("date_") >= 0:
                val = val.isoformat()
            output_data[export_name] = val

        return output_data

    def get_map_full(self):
        themap = self.get_map()

        tags = self.get_tag_map()
        if len(tags) > 0:
            themap["tags"] = tags

        vote = self.get_vote()
        if vote > 0:
            themap["vote"] = tags

        comments = self.get_comment_vec()
        if len(comments) > 0:
            themap["comments"] = comments

        return themap

    def get_archive_link(self):
        from .services.waybackmachine import WaybackMachine
        from .dateutils import DateUtils

        m = WaybackMachine()
        formatted_date = m.get_formatted_date(self.date_published.date())
        archive_link = m.get_archive_url_for_date(formatted_date, self.link)
        return archive_link

    def create_from_youtube(url, data):
        from .pluginentries.youtubelinkhandler import YouTubeLinkHandler

        objs = LinkDataModel.objects.filter(link=url)
        if len(objs) != 0:
            return False

        h = YouTubeLinkHandler(url)
        if not h.download_details():
            PersistentInfo.error("Could not obtain details for link:{}".format(url))
            return False

        data = dict()
        source = h.get_channel_feed_url()
        if source is None:
            PersistentInfo.error("Could not obtain channel feed url:{}".format(url))
            return False

        link = h.get_link_url()
        title = h.get_title()
        description = h.get_description()
        date_published = h.get_datetime_published()
        thumbnail = h.get_thumbnail()
        artist = h.get_channel_name()

        language = "en-US"
        if "language" in data:
            language = data["language"]
        user = None
        if "user" in data:
            user = data["user"]
        persistent = False
        if "persistent" in data:
            persistent = data["persistent"]

        source_obj = None
        sources = SourceDataModel.objects.filter(url=source)
        if sources.exists():
            source_obj = sources[0]

        entry = LinkDataModel(
            source=source,
            title=title,
            description=description,
            link=link,
            date_published=date_published,
            persistent=persistent,
            thumbnail=thumbnail,
            artist=artist,
            language=language,
            user=user,
            source_obj=source_obj,
        )
        entry.save()
        return True

    def get_full_information(data):
        return LinkDataController.update_info(data)

    def update_info(data):
        from .webtools import Page

        p = Page(data["link"])

        data["thumbnail"] = None

        if p.is_youtube():
            LinkDataController.update_info_youtube(data)

        return LinkDataController.update_info_default(data)

    def update_info_youtube(data):
        from .pluginentries.youtubelinkhandler import YouTubeLinkHandler

        h = YouTubeLinkHandler(data["link"])
        h.download_details()

        data["source"] = h.get_channel_feed_url()
        data["link"] = h.get_link_url()
        data["title"] = h.get_title()
        # TODO limit comes from LinkDataModel, do not hardcode
        data["description"] = h.get_description()[:999]
        data["date_published"] = h.get_datetime_published()
        data["thumbnail"] = h.get_thumbnail()

        return data

    def update_info_default(data):
        from .webtools import Page

        p = Page(data["link"])
        if "source" not in data or not data["source"]:
            data["source"] = p.get_domain()
        if "language" not in data or not data["language"]:
            data["language"] = p.get_language()
        if "title" not in data or not data["title"]:
            data["title"] = p.get_title()
        if "description" not in data or not data["description"]:
            data["description"] = p.get_title()
        return data

    def make_not_persistent(self, username):
        tags = LinkTagsDataModel.objects.filter(link_obj=self)
        tags.delete()

        votes = LinkVoteDataModel.objects.filter(link_obj=self)
        votes.delete()

        self.persistent = False
        self.user = username
        self.save()

    def move_to_archive(self):
        objs = ArchiveLinkDataModel.objects.filter(link=self.link)
        if len(objs) == 0:
            themap = self.get_map()
            themap["source_obj"] = self.get_source_obj()
            try:
                ArchiveLinkDataModel.objects.create(**themap)
                self.delete()
            except Exception as e:
                error_text = traceback.format_exc()
        else:
            try:
                self.delete()
            except Exception as e:
                error_text = traceback.format_exc()

    def get_archive_days_limit(self):
        return 100

    def move_all_to_archive():
        from .dateutils import DateUtils

        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=self.get_archive_days_limit() )

        entries = LinkDataController.objects.filter(
            persistent=False, date_published__lt=days_before
        )

        for entry in entries:
            if entry.get_source_obj() is None:
                entry.move_to_archive()
            elif entry.get_source_obj().get_days_to_remove() == 0:
                entry.move_to_archive()


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

            BackgroundJob.write_daily_data_range(date_start, date_stop)
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

    def push_to_repo():
        try:
            items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_PUSH_TO_REPO, subject=""
            )
            if len(items) == 0:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_PUSH_TO_REPO, task=None, subject="", args=""
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
