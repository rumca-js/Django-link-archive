from django.db import models
from django.urls import reverse
from datetime import datetime
import logging
from pytz import timezone



class RssSourceDataModel(models.Model):

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    category = models.CharField(max_length=1000)
    subcategory = models.CharField(max_length=1000)
    dead = models.BooleanField(default = False)
    export_to_cms = models.BooleanField(default = False)
    remove_after_days = models.CharField(max_length=10, default='0')
    language = models.CharField(max_length=1000, default='en-US')
    favicon = models.CharField(max_length=1000, null = True)
    on_hold = models.BooleanField(default = False)

    class Meta:
        ordering = ['title', 'url']

    #def __init__(self, *args, **kwargs):
    #    super().__init__(self, *args, **kwargs)
    #    self.obj = None

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
           mins = time_since_update / timedelta(minutes = 1)

           if mins >= 10:
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
        objs = RssSourceOperationalData.objects.filter(url = self.url)
        if objs.exists():
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
            op = RssSourceOperationalData(url = self.url,
                    date_fetched = date_fetched,
                    import_seconds = import_seconds,
                    number_of_entries = number_of_entries,
                    source_obj = self)
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


class RssSourceOperationalData(models.Model):

    url = models.CharField(max_length=2000, unique=True)
    date_fetched = models.DateTimeField(null = True)
    import_seconds = models.IntegerField(null = True)
    number_of_entries = models.IntegerField(null = True)
    source_obj = models.ForeignKey(RssSourceDataModel, on_delete=models.SET_NULL, related_name='dynami_cdata', null=True, blank=True)


class RssSourceImportHistory(models.Model):
    url = models.CharField(max_length=2000)
    date = models.DateField()
    source_obj = models.ForeignKey(RssSourceDataModel, on_delete=models.SET_NULL, related_name='history_import', null=True, blank=True)


class RssSourceExportHistory(models.Model):
    date = models.DateField()


class RssSourceEntryDataModel(models.Model):

    source = models.CharField(max_length=2000)
    title = models.CharField(max_length=1000)
    description = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000, unique=True)
    date_published = models.DateTimeField(default = datetime.now)
    # this entry cannot be removed
    persistent = models.BooleanField(default = False)
    # this entry is dead indication
    dead = models.BooleanField(default = False)
    # user who added entry
    user = models.CharField(max_length=1000, null = True)

    # possible values en-US, or pl_PL
    language = models.CharField(max_length=10, null = True)
    
    source_obj = models.ForeignKey(RssSourceDataModel, on_delete=models.SET_NULL, related_name='entries', null=True, blank=True)

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
        return RssEntryTagsDataModel.get_tag_string(self.link)

    def get_tag_map(self):
        # TODO should it be done by for tag in self.tags: tag.get_map()?
        result = []
        tags = RssEntryTagsDataModel.objects.filter(link = self.link)
        if tags.exists():
            for tag in tags:
                result.append(tag.tag)
        return result

    def get_comment_map(self):
        # TODO
        return []

    def get_author_tag_string(self):
        return RssEntryTagsDataModel.get_author_tag_string(self.link)

    def update_language(self):
        objs = RssSourceDataModel.objects.filter(url = self.source)
        if objs.exists():
            self.language = objs[0].language
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

    def get_map(self):
        data = {}
        data['source'] = self.source
        data['link'] = self.link
        data['title'] = self.title
        data['date_published'] = str(self.date_published)
        data['description'] = self.description
        data['persistent'] = self.persistent
        data['language'] = self.language
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

    def get_handler_text(self):
        if self.has_handler():
            from .linkhandlers.youtubelinkhandler import YouTubeLinkHandler
            handler = YouTubeLinkHandler(self.link)
            return handler.get_frame()

    def has_handler(self):
        if self.link.find("youtube") >= 0:
            return True
 
    def get_archive_link(self):
        from .sources.waybackmachine import WaybackMachine
        from .dateutils import DateUtils
        m = WaybackMachine()
        formatted_date = m.get_formatted_date(DateUtils.get_date_today())

        archive_link = "https://web.archive.org/web/{}000000*/{}".format(formatted_date, self.link)
        return archive_link


class RssEntryTagsDataModel(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields

    link = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    date = models.DateTimeField(default = datetime.now)

    # You can label entry as 'cringe', 'woke', 'propaganda', 'misinformation'
    # If there are many labels, it will be visible for what it is
    tag = models.CharField(max_length=1000)
    
    link_obj = models.ForeignKey(RssSourceEntryDataModel, on_delete=models.CASCADE, related_name='tags', null=True, blank=True)

    def get_delim():
        return ","

    def join_elements(elements):
        tag_string = ""
        for element in elements:
            if tag_string == "":
                tag_string = element.tag
            else:
                tag_string += RssEntryTagsDataModel.get_delim() + element.tag

        return tag_string

    def get_author_tag_string(author, link):
        current_tags_objs = RssEntryTagsDataModel.objects.filter(link = link, author = author)

        if current_tags_objs.exists():
            return RssEntryTagsDataModel.join_elements(current_tags_objs)

    def get_tag_string(link):
        current_tags_objs = RssEntryTagsDataModel.objects.filter(link = link)

        if current_tags_objs.exists():
            return RssEntryTagsDataModel.join_elements(current_tags_objs)


class RssEntryCommentDataModel(models.Model):

    author = models.CharField(max_length=1000)
    comment = models.TextField(max_length=3000)
    date_published = models.DateTimeField(default = datetime.now)
    date_edited = models.DateTimeField(null = True)
    reply_id = models.IntegerField(null=True)
    link = models.CharField(max_length=1000)
    
    link_obj = models.ForeignKey(RssSourceEntryDataModel, on_delete=models.CASCADE, related_name='comments', null=True, blank=True)


class ConfigurationEntry(models.Model):
    git_path = models.CharField(default = ".", max_length=2000)
    git_user = models.CharField(default = "", max_length=2000)
    git_token = models.CharField(default = "", max_length=2000)
    git_repo = models.CharField(default = "", max_length=2000)
    git_daily_repo = models.CharField(default = "", max_length=2000)

    def is_git_set(self):
        if self.git_repo != "" and self.git_user != "" and self.git_token != "":
            return True
        else:
            return False

    def is_git_daily_set(self):
        if self.git_daily_repo != "" and self.git_user != "" and self.git_token != "":
            return True
        else:
            return False


class PersistentInfo(models.Model):
    info = models.CharField(default = "", max_length=2000)
    level = models.IntegerField(default = 0)
    date = models.DateTimeField(default = datetime.now)
    user = models.CharField(max_length=1000, null = True)

    def create(info, level = int(logging.INFO), date = datetime.now(timezone('UTC')), user = None):
        ob = PersistentInfo(info = info, level = level, date = date, user = user)

        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def text(info, level = int(logging.INFO), date = datetime.now(timezone('UTC')), user = None):
        ob = PersistentInfo(info = info, level = level, date = date, user = user)
        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def error(info, level = int(logging.ERROR), date = datetime.now(timezone('UTC')), user = None):
        ob = PersistentInfo(info = info, level = level, date = date, user = user)
        index = 0
        while index < 5:
            try:
                ob.save()
                return
            except Exception as e:
                index += 1

    def cleanup():
        obs = PersistentInfo.objects.filter(level = int(logging.INFO))
        if obs.exists():
            obs.delete()

    def truncate():
        PersistentInfo.objects.all().delete()


## YouTube meta cache
class YouTubeMetaCache(models.Model):

    url = models.CharField(max_length=1000, help_text='url', unique=False)
    details_json = models.CharField(max_length=1000, help_text='details_json')
    dead = models.BooleanField(default = False, help_text='dead')

    link_yt_obj = models.ForeignKey(RssSourceEntryDataModel, on_delete=models.SET_NULL, related_name='link_yt', null=True, blank=True)

class YouTubeReturnDislikeMetaCache(models.Model):
    url = models.CharField(max_length=1000, help_text='url', unique=False)
    return_dislike_json = models.CharField(max_length=1000, help_text='return_dislike_json')
    dead = models.BooleanField(default = False, help_text='dead')

    link_rd_obj = models.ForeignKey(RssSourceEntryDataModel, on_delete=models.SET_NULL, related_name='link_rd', null=True, blank=True)
