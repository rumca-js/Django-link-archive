from django.db import models
from django.urls import reverse
from datetime import datetime
import logging


class PageParser(object):
    def __init__(self, link_url):
        self.title = self.process(self.get_page(link_url))

    def process(self, text):
        title = ""

        titles = []
        for text in re.findall("<title.*?>(.+?)</title>"):
            titles.append(text)

        return " ".join(titles)

    def get_page(url):
        import urllib.request, urllib.error, urllib.parse
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            webContent = urllib.request.urlopen(req).read().decode('UTF-8')
            return webContent
        except Exception as e:
           logging.critical(e, exc_info=True)


class RssSourceDataModel(models.Model):

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    category = models.CharField(max_length=1000)
    subcategory = models.CharField(max_length=1000)
    date_fetched = models.DateTimeField(null = True)
    dead = models.BooleanField(default = False)
    export_to_cms = models.BooleanField(default = True)
    remove_after_days = models.CharField(max_length=10, default='0')
    language = models.CharField(max_length=1000, default='en-US')

    class Meta:
        ordering = ['title', 'url', 'date_fetched']

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



class RssSourceEntryDataModel(models.Model):

    source = models.CharField(max_length=2000)
    title = models.CharField(max_length=1000)
    description = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000, unique=True)
    date_published = models.DateTimeField(default = datetime.now)
    persistent = models.BooleanField(default = False)
    dead = models.BooleanField(default = False) # indicated that is removed, fetching will not re-add it

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


class RssEntryTagsDataModel(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields

    link = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    date = models.DateTimeField(default = datetime.now)

    # You can label entry as 'cringe', 'woke', 'propaganda', 'misinformation'
    # If there are many labels, it will be visible for what it is
    tag = models.CharField(max_length=1000)

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
    git_repo = models.CharField(default = "", max_length=2000)
    git_user = models.CharField(default = "", max_length=2000)
    git_token = models.CharField(default = "", max_length=2000)

    def is_git_set(self):
        if self.git_repo != "" and self.git_user != "" and self.git_token != "":
            return True
        else:
            return False
