from django.db import models
from django.urls import reverse
from datetime import datetime


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


class RssLinkDataModel(models.Model):

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    category = models.CharField(max_length=1000)
    subcategory = models.CharField(max_length=1000)
    date_fetched = models.DateTimeField(null = True)
    dead = models.BooleanField(default = False)

    class Meta:
        ordering = ['url', 'title', 'date_fetched']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:source-detail', args=[str(self.id)])


class RssLinkEntryDataModel(models.Model):

    url = models.CharField(max_length=2000)
    title = models.CharField(max_length=1000)
    description = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000, unique=True)
    date_published = models.DateTimeField(default = datetime.now)
    favourite = models.BooleanField(default = False)

    class Meta:
        ordering = ['-date_published', 'url', 'title']

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse('rsshistory:entry-detail', args=[str(self.id)])


class ConfigurationEntry(models.Model):
    git_path = models.CharField(max_length=2000)
    git_repo = models.CharField(max_length=2000)
    git_user = models.CharField(max_length=2000)
    git_token = models.CharField(max_length=2000)


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
        self.sources = []

        for link_row in links:
             link_row = link_row.replace("\r", "")
             link = SourceConverter(link_row)
             self.sources.append(link)

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
        from urllib.parse import urlparse
        delimiter = ";"
        link_info = row_data.split(delimiter)

        self.title = ""
        self.date_published = datetime.now
        self.url = ""
        self.favourite = True
        self.description = ""

        self.link = link_info[0]

        if len(link_info) > 1:
            if len(link_info[1].strip()) > 0:
                self.title = link_info[1]
        else:
            parser = PageParser(self.link)
            self.title = parser.title

        if len(link_info) > 2:
            if len(link_info[2].strip()) > 0:
                self.date_published = link_info[2]

        if len(link_info) > 3:
            if len(link_info[3].strip()) > 0:
                self.url = link_info[3]
            else:
                self.url = urlparse(self.link).netloc
        else:
            if len(self.link) > 4:
                self.url = urlparse(self.link).netloc

        if len(link_info) > 4:
            self.favourite = link_info[4] == "True"

        if len(link_info) > 5:
            if len(link_info[5].strip()) > 0:
                self.description = link_info[5]

    def get_text(link):
        data = {}
        data['url'] = link.url
        data['link'] = link.link
        data['title'] = link.title
        data['date_published'] = str(link.date_published)
        data['description'] = link.description

        return data

    def get_csv_text(link):
        return "{0};{1};{2};{3};{4};{5}".format(link.link, link.url, link.favourite, link.title, link.date_published, link.description)

    def get_clean_text(link):
        return "{0}\n{1}\n{2}\n{3}\n{4}\n{5}\n".format(link.url, link.link, link.title, link.date_published, link.favourite, link.description)

    def get_md_text(link):
        return "# {0}\n - {1}\n - RSS feed: {2}\n - date published: {3}\n - Starred: {4}\n\n{5}\n".format(link.title, link.link, link.url, link.date_published, link.favourite, link.description)


class EntriesConverter(object):

    def __init__(self, data = None):
        if data:
            self.process_string(data)

    def process_string(self, data):
        delimiter = "\n"
        entries = data.split(delimiter)
        self.entries = []

        for entry_row in entries:
             entry_row = entry_row.replace("\r", "")
             entry = EntryConverter(entry_row)
             self.entries.append(entry)

    def set_entries(self, entries):
        self.entries = entries

    def get_text(self):
        output_data = []
        for entry in self.entries:
            entry_data = EntryConverter.get_text(entry)
            output_data.append(entry_data)
            
        import json
        return json.dumps(output_data)

    def get_csv_text(self):
        output_data = []
        for entry in self.entries:
            entry_data = EntryConverter.get_csv_text(entry)
            output_data.append(entry_data)
            
        return "\n".join(output_data)

    def get_clean_text(self):
        output_data = []
        for entry in self.entries:
            entry_data = EntryConverter.get_clean_text(entry)
            output_data.append(entry_data)
            
        return "\n".join(output_data)

    def get_md_text(self):
        output_data = []
        for entry in self.entries:
            entry_data = EntryConverter.get_md_text(entry)
            output_data.append(entry_data)
            
        return "\n".join(output_data)
