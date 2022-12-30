from django.db import models
from django.urls import reverse
from datetime import datetime
import logging



class RssSourceDataModel(models.Model):

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    category = models.CharField(max_length=1000)
    subcategory = models.CharField(max_length=1000)
    dead = models.BooleanField(default = False)
    export_to_cms = models.BooleanField(default = True)
    remove_after_days = models.CharField(max_length=10, default='0')
    language = models.CharField(max_length=1000, default='en-US')

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
                    number_of_entries = number_of_entries)
            op.save()


class RssSourceOperationalData(models.Model):

    url = models.CharField(max_length=2000, unique=True)
    date_fetched = models.DateTimeField(null = True)
    import_seconds = models.IntegerField(null = True)
    number_of_entries = models.IntegerField(null = True)


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
    
    source_obj = models.ForeignKey(RssSourceDataModel, on_delete=models.CASCADE, related_name='entries', null=True, blank=True)

    class Meta:
        ordering = ['-date_published', 'source', 'title']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:entry-detail', args=[str(self.id)])

    def get_source_name(self):
        sources = RssSourceDataModel.objects.filter(url = self.source)
        if len(sources) > 0:
            return sources[0].title
        else:
            return self.source

    def get_tag_string(self):
        return RssEntryTagsDataModel.get_tag_string(self.link)

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



class RssEntryCommentsDataModel(models.Model):

    link = models.CharField(max_length=1000, unique=True)
    comment = models.CharField(max_length=1000)
    reply_id = models.CharField(max_length=1000) # comment id to which we reply
    author = models.CharField(max_length=1000)
    date_published = models.DateTimeField(default = datetime.now)
    date_edited = models.DateTimeField(null = True)


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


from pytz import timezone

class PersistentInfo(models.Model):
    info = models.CharField(default = "", max_length=2000)
    level = models.IntegerField(default = 0)
    date = models.DateTimeField(default = datetime.now)
    user = models.CharField(max_length=1000, null = True)

    def create(info, level = int(logging.INFO), date = datetime.now(timezone('UTC')), user = None):
        ob = PersistentInfo(info = info, level = level, date = date, user = user)
        ob.save()

    def error(info, level = int(logging.ERROR), date = datetime.now(timezone('UTC')), user = None):
        ob = PersistentInfo(info = info, level = level, date = date, user = user)
        ob.save()

    def cleanup():
        obs = PersistentInfo.objects.filter(level = int(logging.INFO))
        if obs.exists():
            obs.delete()
