from django.db import models
from django.urls import reverse
from datetime import datetime


class RssLinkDataModel(models.Model):

    url = models.TextField(max_length=2000, help_text='url', unique=True)
    title = models.TextField(max_length=1000, help_text='title')
    category = models.TextField(max_length=1000, help_text='category')
    subcategory = models.TextField(max_length=1000, help_text='subcategory')
    date_fetched = models.DateTimeField(null = True)

    class Meta:
        ordering = ['url', 'title', 'date_fetched']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:link-detail', args=[str(self.id)])


class RssLinkEntryDataModel(models.Model):

    url = models.TextField(max_length=2000, help_text='url')
    title = models.TextField(max_length=1000, help_text='title')
    description = models.TextField(max_length=1000, help_text='description')
    link = models.TextField(max_length=1000, help_text='link', unique=True)
    date_published = models.DateTimeField(default = datetime.now, help_text = "date_published")
    favourite = models.BooleanField(default = False, help_text = "favourite")

    class Meta:
        ordering = ['-date_published', 'url', 'title']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:entry-detail', args=[str(self.id)])


class SourceConverter(object):
    def __init__(self, row_data):
        self.process_string(row_data)

    def process_string(self, row_data):
         delimiter = ";"
         link_info = row_data.split(delimiter)

         self.url = link_info[0]
         self.title = link_info[1]
         self.category = link_info[2]
         self.subcategory = link_info[3]
         self.date_fetched = link_info[4]

    def get_text(link):
        return "{0};{1};{2};{3};{4}".format(link.url, link.title, link.category, link.subcategory, link.date_fetched)


class SourcesConverter(object):

    def __init__(self, data = None):
        if data:
            self.process_string(data)

    def process_string(self, data):
        delimiter = "\n"
        links = data.split(delimiter)
        self.links = []

        for link_row in links:
             link_row = link_row.replace("\r", "")
             link = SourceConverter(link_row)
             self.links.append(link)

    def set_sources(self, sources):
        self.sources = sources

    def get_text(self):
        summary_text = ""
        for source in self.sources:
            data = SourceConverter.get_text(source)
            summary_text += data + "\n"
        return summary_text


class EntryConverter(object):
    def __init__(self, row_data):
        self.process_string(row_data)

    def process_string(self, row_data):
         delimiter = ";"
         link_info = row_data.split(delimiter)

         self.url = link_info[0]
         self.title = link_info[1]
         self.description = link_info[2]
         self.link = link_info[3]
         self.date_published = link_info[4]
         self.favourite = link_info[5]

    def get_text(link):
        data = {}
        data['url'] = link.url
        data['title'] = link.title
        data['description'] = link.description
        data['link'] = link.link
        data['date_published'] = str(link.date_published)

        return data

        #return "{0};{1};{2};{3};{4};{5}".format(link.url, link.title, link.description, link.link, link.date_published, link.favourite)


class EntriesConverter(object):

    def __init__(self, data = None):
        if data:
            self.process_string(data)

    def process_string(self, data):
        delimiter = "\n"
        links = data.split(delimiter)
        self.links = []

        for link_row in links:
             link_row = link_row.replace("\r", "")
             link = EntryConverter(link_row)
             self.links.append(link)

    def set_entries(self, entries):
        self.entries = entries

    def get_text(self):
        summary_text = ""

        output_data = []
        for entry in self.entries:
            entry_data = EntryConverter.get_text(entry)
            output_data.append(entry_data)
            
        import json
        return json.dumps(output_data)
