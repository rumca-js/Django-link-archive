import traceback
import logging
from datetime import datetime, date

from django.db import models
from django.urls import reverse

from pytz import timezone


class SourceDataModel(models.Model):
    SOURCE_TYPE_RSS = "source-type-rss"
    SOURCE_TYPE_PARSE = "source-type-parse"

    SOURCE_TYPES = (
        (SOURCE_TYPE_RSS, SOURCE_TYPE_RSS),            # 
        (SOURCE_TYPE_PARSE, SOURCE_TYPE_PARSE),        # 
        )

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    category = models.CharField(max_length=1000)
    subcategory = models.CharField(max_length=1000)
    dead = models.BooleanField(default=False)
    export_to_cms = models.BooleanField(default=False)
    remove_after_days = models.CharField(max_length=10, default='0')
    language = models.CharField(max_length=1000, default='en-US')
    favicon = models.CharField(max_length=1000, null=True)
    on_hold = models.BooleanField(default=False)
    fetch_period = models.IntegerField(default=3600)
    source_type = models.CharField(max_length=1000, null=False, choices = SOURCE_TYPES, default=SOURCE_TYPE_RSS)

    class Meta:
        ordering = ['title']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:source-detail', args=[str(self.id)])

    def get_days_to_remove(self):
        days = 0
        try:
            days = int(self.remove_after_days)
        except:
            pass

        return days

    def is_fetch_possible(self):
        from datetime import timedelta
        from .dateutils import DateUtils

        if self.on_hold:
            return False

        start_time = DateUtils.get_datetime_now_utc()

        date_fetched = self.get_date_fetched()
        if date_fetched:
            time_since_update = start_time - date_fetched
            #mins = time_since_update / timedelta(minutes=1)
            secs = time_since_update / timedelta(seconds=1)

            #if mins >= 30:
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
            objs = SourceOperationalData.objects.filter(url = self.url, source_obj = None)
            if len(objs) >= 0:
                objs.delete()

            op = SourceOperationalData(url=self.url,
                                          date_fetched=date_fetched,
                                          import_seconds=import_seconds,
                                          number_of_entries=number_of_entries,
                                          source_obj=self)
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

    def get_map(self):
        output_data = {}

        output_data['url'] = self.url
        output_data['title'] = self.title
        output_data['category'] = self.category
        output_data['subcategory'] = self.subcategory
        output_data['dead'] = self.dead
        output_data['export_to_cms'] = self.export_to_cms
        output_data['remove_after_days'] = self.remove_after_days
        output_data['language'] = self.language
        output_data['favicon'] = self.favicon
        output_data['on_hold'] = self.on_hold

        return output_data

    def get_map_full(self):
        return self.get_map()


class SourceOperationalData(models.Model):
    url = models.CharField(max_length=2000, unique=True)
    date_fetched = models.DateTimeField(null=True)
    import_seconds = models.IntegerField(null=True)
    number_of_entries = models.IntegerField(null=True)
    source_obj = models.ForeignKey(SourceDataModel, on_delete=models.SET_NULL, related_name='dynamic_data',
                                   null=True, blank=True)

    class Meta:
        ordering = ['date_fetched']


class RssSourceImportHistory(models.Model):
    url = models.CharField(max_length=2000)
    date = models.DateField()
    source_obj = models.ForeignKey(SourceDataModel, on_delete=models.SET_NULL, related_name='history_import',
                                   null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def get_safe():
        return RssSourceImportHistory.objects.all()[:100]


class RssSourceExportHistory(models.Model):
    date = models.DateField()

    class Meta:
        ordering = ['-date']

    def is_update_required():
        from .dateutils import DateUtils
        try:
            ob = ConfigurationEntry.get()
            if not ob.is_git_set():
                return

            yesterday = DateUtils.get_date_yesterday()

            history = RssSourceExportHistory.objects.filter(date=yesterday)

            if len(history) != 0:
                return False
            return True

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error("Exception for update: {0} {1}".format(str(e), error_text))

    def get_safe():
        return RssSourceExportHistory.objects.all()[:100]


class LinkDataModel(models.Model):
    source = models.CharField(max_length=2000)
    title = models.CharField(max_length=1000, null=True)
    description = models.CharField(max_length=1000, null=True)
    link = models.CharField(max_length=1000, unique=True)
    date_published = models.DateTimeField(default=datetime.now)
    # this entry cannot be removed
    persistent = models.BooleanField(default=False)
    # this entry is dead indication
    dead = models.BooleanField(default=False)
    artist = models.CharField(max_length=1000, null=True, default=None)
    album = models.CharField(max_length=1000, null=True, default=None)
    # user who added entry
    user = models.CharField(max_length=1000, null=True, default=None)

    # possible values en-US, or pl_PL
    language = models.CharField(max_length=10, null=True, default=None)
    thumbnail = models.CharField(max_length=1000, null=True, default=None)

    source_obj = models.ForeignKey(SourceDataModel, on_delete=models.SET_NULL, related_name='link_source', null=True,
                                   blank=True)

    class Meta:
        ordering = ['-date_published', 'source', 'title']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:entry-detail', args=[str(self.id)])

    def get_source_name(self):
        if self.source_obj:
            return self.source_obj.title
        else:
            return self.source

    def get_tag_string(self):
        return LinkTagsDataModel.join_elements(self.tags.all()) 

    def get_tag_map(self):
        # TODO should it be done by for tag in self.tags: tag.get_map()?
        result = []
        tags = self.tags.all()
        for tag in tags:
            result.append(tag.tag)
        return result

    def get_comment_map(self):
        # TODO
        return []

    def update_language(self):
        if self.source_obj:
            self.language = self.source_obj.language
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
        if self.source_obj:
            return self.source_obj.get_favicon()

        from .webtools import Page
        page = Page(self.link)
        domain = page.get_domain()
        return domain + "/favicon.ico"

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail

        return self.get_favicon()

    def get_map(self):
        data = {}
        data['source'] = self.source
        data['link'] = self.link
        data['title'] = self.title
        data['date_published'] = str(self.date_published)
        data['description'] = self.description
        data['persistent'] = self.persistent
        data['language'] = self.language
        data['thumbnail'] = self.thumbnail
        data['user'] = self.user

        return data

    def get_map_full(self):
        themap = self.get_map()

        tags = self.get_tag_map()
        if len(tags) > 0:
            themap['tags'] = tags

        comments = self.get_comment_map()
        if len(comments) > 0:
            themap['comments'] = comments

        return themap

    def get_archive_link(self):
        from .sources.waybackmachine import WaybackMachine
        from .dateutils import DateUtils
        m = WaybackMachine()
        formatted_date = m.get_formatted_date(self.date_published.date())

        archive_link = "https://web.archive.org/web/{}000000*/{}".format(formatted_date, self.link)
        return archive_link

    def create_from_youtube(url, data):
        from .handlers.youtubelinkhandler import YouTubeLinkHandler

        objs = LinkDataModel.objects.filter(link = url)
        if len(objs) != 0:
           return

        h = YouTubeLinkHandler(url)
        h.download_details()

        data = dict()
        source = h.get_channel_feed_url()
        if source is None:
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
        sources = SourceDataModel.objects.filter(url = source)
        if sources.exists():
            source_obj = sources[0]

        entry = LinkDataModel(
                source = source,
                title = title,
                description = description,
                link = link,
                date_published = date_published,
                persistent = persistent,
                thumbnail = thumbnail,
                artist = artist,
                language = language,
                user = user,
                source_obj = source_obj)
        entry.save()
        return True


class LinkTagsDataModel(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields

    link = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    date = models.DateTimeField(default=datetime.now)

    # You can label entry as 'cringe', 'woke', 'propaganda', 'misinformation'
    # If there are many labels, it will be visible for what it is
    tag = models.CharField(max_length=1000)

    link_obj = models.ForeignKey(LinkDataModel, on_delete=models.CASCADE, related_name='tags', null=True,
                                 blank=True)

    def get_delim():
        return ","

    def join_elements(elements):
        tag_string = ""
        for element in elements:
            if tag_string == "":
                tag_string = element.tag
            else:
                tag_string += LinkTagsDataModel.get_delim() + element.tag

        return tag_string

    def get_author_tag_string(author, link):
        current_tags_objs = LinkTagsDataModel.objects.filter(link=link, author=author)

        if current_tags_objs.exists():
            return LinkTagsDataModel.join_elements(current_tags_objs)


class LinkCommentDataModel(models.Model):
    author = models.CharField(max_length=1000)
    comment = models.TextField(max_length=3000)
    date_published = models.DateTimeField(default=datetime.now)
    date_edited = models.DateTimeField(null=True)
    reply_id = models.IntegerField(null=True)
    link = models.CharField(max_length=1000)

    link_obj = models.ForeignKey(LinkDataModel, on_delete=models.CASCADE, related_name='comments', null=True,
                                 blank=True)


class ConfigurationEntry(models.Model):
    data_import_path = models.CharField(default="./data/imports", max_length=2000, null=True)
    data_export_path = models.CharField(default="./data/exports", max_length=2000, null=True)
    git_path = models.CharField(default="./data/git", max_length=2000, null=True)
    git_user = models.CharField(default="", max_length=2000, null=True)
    git_token = models.CharField(default="", max_length=2000, null=True)
    git_repo = models.CharField(default="", max_length=2000, null=True)
    git_daily_repo = models.CharField(default="", max_length=2000, null=True)
    sources_refresh_period = models.IntegerField(default=3600)
    link_archive = models.BooleanField(default=True)
    source_archive = models.BooleanField(default=True)

    def get():
        confs = ConfigurationEntry.objects.all()
        if len(confs) == 0:
            return ConfigurationEntry.objects.create()
        else:
            return confs[0]

    def is_git_set(self):
        if self.git_repo == "" or self.git_user == "" and self.git_token == "" or self.git_repo == None or self.git_user == None or self.git_token == None:
            return False
        else:
            return True

    def is_git_daily_set(self):
        if self.git_daily_repo == "" or self.git_user == "" or self.git_token == "" or self.git_daily_repo == None or self.git_user == None or self.git_token == None:
            return False
        else:
            return True

    def get_data_export_path(self):
        return self.data_export_path


class UserConfig(models.Model):
    THEME_TYPE_CHOICES = (
        ('light', 'light'),
        ('dark', 'dark'),
    )

    DISPLAY_TYPE_CHOICES = (
        ('std', 'standard'),
        ('tags', 'clickable-tags'),
        ('twolines', 'line-and-buttons'),
    )

    user = models.CharField(max_length=500, unique=True)
    # theme: light, dark
    theme = models.CharField(max_length=500, null=True, default="light", choices = THEME_TYPE_CHOICES)
    # display type: standard, compact, preview
    display_type = models.CharField(max_length=500, null=True, default="standard", choices = DISPLAY_TYPE_CHOICES)
    show_icons = models.BooleanField(default=True)
    thumbnails_as_icons = models.BooleanField(default=True)
    small_icons = models.BooleanField(default=True)
    links_per_page = models.IntegerField(default=100)

    def get():
        confs = UserConfig.objects.all()
        if len(confs) == 0:
            return UserConfig()
        else:
            return confs[0]


class PersistentInfo(models.Model):
    info = models.CharField(default="", max_length=2000)
    level = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.now)
    user = models.CharField(max_length=1000, null=True)

    def create(info, level=int(logging.INFO), user=None):
        ob = PersistentInfo(info=info, level=level, date=datetime.now(timezone('UTC')), user=user)

        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def text(info, level=int(logging.INFO), user=None):
        ob = PersistentInfo(info=info, level=level, date=datetime.now(timezone('UTC')), user=user)
        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def error(info, level=int(logging.ERROR), user=None):
        ob = PersistentInfo(info=info, level=level, date=datetime.now(timezone('UTC')), user=user)
        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def exc(info, level=int(logging.ERROR), exc_data=None, user=None):
        text = "{}. Exception data:\n{}".format(info, str(exc_data))
        ob = PersistentInfo(info=text, level=level, date=datetime.now(timezone('UTC')), user=user)

        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def cleanup():
        obs = PersistentInfo.objects.filter(level=int(logging.INFO))
        if obs.exists():
            obs.delete()

    def truncate():
        PersistentInfo.objects.all().delete()

    def get_safe():
        return PersistentInfo.objects.all()[0:100]


""" YouTube meta cache """

class YouTubeMetaCache(models.Model):
    url = models.CharField(max_length=1000, help_text='url', unique=False)
    details_json = models.CharField(max_length=1000, help_text='details_json')
    dead = models.BooleanField(default=False, help_text='dead')

    link_yt_obj = models.ForeignKey(LinkDataModel, on_delete=models.SET_NULL, related_name='link_yt',
                                    null=True, blank=True)


class YouTubeReturnDislikeMetaCache(models.Model):
    url = models.CharField(max_length=1000, help_text='url', unique=False)
    return_dislike_json = models.CharField(max_length=1000, help_text='return_dislike_json')
    dead = models.BooleanField(default=False, help_text='dead')

    link_rd_obj = models.ForeignKey(LinkDataModel, on_delete=models.SET_NULL, related_name='link_rd',
                                    null=True, blank=True)


class BackgroundJob(models.Model):
    JOB_PROCESS_SOURCE = "process-source"
    JOB_LINK_ADD = "link-add"
    JOB_LINK_DETAILS = "link-details"
    JOB_LINK_REFRESH = "link-refresh"
    JOB_LINK_ARCHIVE = "link-archive"
    JOB_LINK_DOWNLOAD = "link-download"
    JOB_LINK_DOWNLOAD_MUSIC = "download-music"
    JOB_LINK_DOWNLOAD_VIDEO = "download-video"
    JOB_WRITE_DAILY_DATA = "write-daily-data"
    JOB_WRITE_TOPIC_DATA = "write-topic-data"
    JOB_WRITE_BOOKMARKS = "write-bookmarks"
    JOB_PUSH_TO_REPO = "push-to-repo"

    JOB_CHOICES = (
        (JOB_PROCESS_SOURCE, JOB_PROCESS_SOURCE),        # for RSS sources it checks if there are new data
        (JOB_LINK_ADD, JOB_LINK_ADD),                    # adds link using default properties
        (JOB_LINK_DETAILS, JOB_LINK_DETAILS),            # fetches link additional information
        (JOB_LINK_REFRESH, JOB_LINK_REFRESH),            # refreshes link, refetches its data
        (JOB_LINK_ARCHIVE, JOB_LINK_ARCHIVE),            # link is archived using thirdparty pages (archive.org)
        (JOB_LINK_DOWNLOAD, JOB_LINK_DOWNLOAD),          # link is downloaded using wget
        (JOB_LINK_DOWNLOAD_MUSIC, JOB_LINK_DOWNLOAD_MUSIC),        # 
        (JOB_LINK_DOWNLOAD_VIDEO, JOB_LINK_DOWNLOAD_VIDEO),        # 
        (JOB_WRITE_DAILY_DATA, JOB_WRITE_DAILY_DATA),    # writes daily data
        (JOB_WRITE_TOPIC_DATA, JOB_WRITE_TOPIC_DATA),    # writes topic data
        (JOB_WRITE_BOOKMARKS, JOB_WRITE_BOOKMARKS),      # writes bookmarks
        (JOB_PUSH_TO_REPO, JOB_PUSH_TO_REPO),            # pushes to repo
        )

    # job - add link, process source, download music, download video, wayback save
    job = models.CharField(max_length=1000, null=False, choices = JOB_CHOICES)
    # task name
    task = models.CharField(max_length=1000, null=True)
    subject = models.CharField(max_length=1000, null=False)
    # task args "subject,arg1,arg2,..."
    # for add link, the first argument is the link URL
    # for download music, the first argument is the link URL
    args = models.CharField(max_length=1000, null=True)

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
                job.delete()

    def get_number_of_jobs(job_type):
        return len(BackgroundJob.objects.filter(job=job_type))

    def download_rss(source, force = False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        if len(BackgroundJob.objects.filter(job=BackgroundJob.JOB_PROCESS_SOURCE, subject=source.url)) == 0: 
            BackgroundJob.objects.create(job=BackgroundJob.JOB_PROCESS_SOURCE, task=None, subject=source.url, args="")

        return True

    def write_daily_data(date_start=date.today(), date_stop=date.today()):
        from datetime import timedelta
        try:
            if date_stop < date_start:
                PersistentInfo.error("Yearly generation: Incorrect configuration of dates start:{} stop:{}".format(date_start, date_stop))
                return False

            sent = False
            current_date = date_start
            while current_date <= date_stop:
                str_date = current_date.isoformat()
                current_date += timedelta(days = 1) 

                BackgroundJob.objects.create(job='write-daily-data', task=None, subject=str_date, args="")
                sent = True

            return sent
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Daily data: {} {}".format(str(e), error_text))

    def write_daily_data_str(start='2022-01-01', stop = '2022-12-31'):
        try:
            date_start = datetime.strptime(start, '%Y-%m-%d').date()
            date_stop = datetime.strptime(stop, '%Y-%m-%d').date()

            BackgroundJob.write_daily_data(date_start, date_stop)
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Daily data: {} {}".format(str(e), error_text))

    def write_tag_data(tag):
        try:
            BackgroundJob.objects.create(job=JOB_WRITE_TOPIC_DATA, task=None, subject=tag, args="")
            return True
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Tag data: {} {}".format(str(e), error_text))

    def write_bookmarks():
        try:
            BackgroundJob.objects.create(job=JOB_WRITE_BOOKMARKS, task=None, subject="", args="")
            return True
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Write bookmarks: {} {}".format(str(e), error_text))

    def link_archive(link_url):
        try:
            BackgroundJob.objects.create(job=JOB_LINK_ARCHIVE, task=None, subject=link_url, args="")
            return True
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Link archive: {} {}".format(str(e), error_text))

    def link_download(link_url):
        try:
            BackgroundJob.objects.create(job=JOB_LINK_DOWNLOAD, task=None, subject=link_url, args="")
            return True
        except Exception as e:
           error_text = traceback.format_exc()
           PersistentInfo.error("Exception: Link download: {} {}".format(str(e), error_text))
