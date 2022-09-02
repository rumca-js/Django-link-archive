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
    date_published = models.DateTimeField(default=datetime.now)

    class Meta:
        ordering = ['-date_published', 'url', 'title']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:link-detail', args=[str(self.id)])


class LinkData(object):
    def __init__(self, row_data):
         delimiter = ";"
         link_info = row_data.split(delimiter)

         self.url = link_info[0]
         self.title = link_info[1]
         self.author = link_info[2]
         self.category = link_info[4]
         self.subcategory = link_info[5]
         self.tag = link_info[6]
         self.date_created = link_info[7]

    def to_string(link):
        return "{0};{1};{2};{3};{4};{5};{6};{7};{8}".format(link.url, link.title, link.author, link.category, link.subcategory, link.tag, link.date_created)


class LinksData(object):
    def __init__(self, data):
        delimiter = "\n"
        links = data.split(delimiter)
        self.links = []

        for link_row in links:
             link_row = link_row.replace("\r", "")
             link = LinkData(link_row)
             self.links.append(link)
