import logging
import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse


class Page(object):
    def __init__(self, url):
        self.url = url
        self.contents = self.get_contents()

    def is_valid(self):
        if self.contents:
            return True
        else:
            return False;

    def get_contents(self):
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            webContent = urllib.request.urlopen(req).read().decode('UTF-8')
            return webContent
        except Exception as e:
           logging.critical(e, exc_info=True)

    def get_language(self):
        if self.contents:
            whlang = self.contents.find("lang")
            if whlang >= 0:
                lang = self.extract_html(self.contents, '"', '"', whlang)

                return lang

    def extract_html(self, text, tag, closingtag, wh = None):
        if not wh:
            wh = 0

        wh = text.find(tag, wh)

        if wh > 0:
            wh2 = text.find(closingtag, len(tag) + wh + 1)

            if wh2 > 0:
                title = text[wh + len(tag):wh2]
                if title.strip() != "":
                    return title

    def get_domain(self):
        items = urlparse(self.url)
        return items.scheme + "://" + items.netloc

    def get_title(self):
        titles = []
        for text in re.findall("<title.*?>(.+?)</title>"):
            titles.append(self.contents)

        return " ".join(titles)

    def get_links(self):
        import re
        import requests
        links = set()

        page = self.get_page(self.searchplace)

        wh = 1
        while wh:
            wh = page.find('<a href="', wh + 1)

            if wh > 0:
                #print(wh)
                text = self.extract_html(page, '<a href="', '"', wh)
                if text:
                    links.add(text)
                #print(text)
            else:
                break

        return links

