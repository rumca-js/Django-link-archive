import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse
import html
import traceback
import requests
import re

from bs4 import BeautifulSoup


class Page(object):
    # use headers from https://www.supermonitoring.com/blog/check-browser-http-headers/
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"
    # user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
    # user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0" # from browser

    def __init__(self, url, contents=None):
        self.url = url
        self.contents = contents
        self.status_code = None

        from .models import ConfigurationEntry
        config = ConfigurationEntry.get()
        self.user_agent = config.user_agent

    def is_valid(self):
        if not self.contents:
            self.contents = self.get_contents()

        if self.contents:
            return True
        else:
            return False

    def try_decode(self, thebytes):
        try:
            return thebytes.decode("UTF-8", errors="replace")
        except Exception as e:
            pass

    def is_status_ok(self):
        if self.status_code is None:
            return False

        print("Status code:{}".format(self.status_code))
        if self.status_code == 403:
            # Many pages return 403, but they are correct
            return True

        return self.status_code >= 200 and self.status_code < 300

    def get_contents(self):
        if self.contents:
            return self.contents

        hdr = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }

        try:
            r = requests.get(self.url, headers=hdr, timeout=5)
            self.status_code = r.status_code
            return r.text

        except Exception as e:
            error_text = traceback.format_exc()
            from .models import PersistentInfo

            PersistentInfo.error(
                "Page: Error while reading page:{};Error:{};{}".format(
                    self.url, str(e), error_text
                )
            )

    def get_language(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return "en"

        soup = BeautifulSoup(self.contents, 'html.parser')
        html = soup.find("html")
        if html and html.has_attr("lang"):
            print("returning: {}".format(html["lang"]))
            return html["lang"]

    def extract_html(self, text, tag, closingtag, wh=None):
        if not wh:
            wh = 0

        wh = text.find(tag, wh)

        if wh > 0:
            wh2 = text.find(closingtag, len(tag) + wh + 1)

            if wh2 > 0:
                title = text[wh + len(tag) : wh2]
                if title.strip() != "":
                    return title

    def get_domain(self):
        items = urlparse(self.url)
        return str(items.scheme) + "://" + str(items.netloc)

    def get_domain_only(self):
        items = urlparse(self.url)
        return str(items.netloc)

    def get_title(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        title = None

        soup = BeautifulSoup(self.contents, 'html.parser')
        title_find = soup.find('title')
        if title_find:
            title = title_find.string

        title_find = soup.find("meta", property="og:title")
        if title_find and title_find.has_attr("content"):
            title = title_find["content"]

        if title:
            title = title.strip()
            return title
        #title = html.unescape(title)

    def get_description(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        description = None

        soup = BeautifulSoup(self.contents, "html.parser")
        description_find = soup.find("meta", attrs={'name' : "description"})
        if description_find and description_fidn.has_attr("content"):
            description = description_find["content"]

        description_find = soup.find("meta", property="og:description")
        if description_find and description_find.has_attr("content"):
            description = description_find["content"]

        if description is None:
            wh1 = self.contents.find('<meta name="description"')
            if wh1 == -1:
                return

            wh1 = self.contents.find('description',wh1 + 24 +1)
            if wh1 == -1:
                return
            wh1 = self.contents.find('"',wh1+1)
            if wh1 == -1:
                return
            wh2 = self.contents.find('"',wh1+1)
            if wh2 == -1:
                return
            description = self.contents[wh1+1: wh2]

        if description:
            description = description.strip()

        return description

    def is_link_valid(self, address):
        return self.is_link_valid_domain(address)

    def is_link_valid_domain(self, address):
        if not address.startswith(self.get_domain()):
            return False
        return True

    def is_rss_available(self):
        if self.get_contents().find("application/rss+xml") >= 0:
            return True
        return False

    def get_links(self):
        return self.get_links_re()

    def get_links_re(self):
        links = set()

        cont = str(self.get_contents())
        url = self.url
        if url.find("?") >= 0:
            wh = url.find("?")
            url = url[:wh]

        allt = re.findall("(https?://[a-zA-Z0-9./\-_]+)", cont)
        links.update(set(allt))

        allt2 = re.findall('href="([a-zA-Z0-9./\-_]+)', cont)
        for item in allt2:
            if item.find("http") == 0:
                ready_url = item
            else:
                if item.startswith("//"):
                    ready_url = "https:" + item
                else:
                    if not url.endswith("/"):
                        url = url + "/"
                    if item.startswith("/"):
                        item = item[1:]

                    ready_url = url + item

            links.add(ready_url)

        return links

    def is_mainstream(self):
        dom = self.get_domain_only()

        # wallet gardens which we will not accept

        mainstream = [
            "www.facebook",
            "www.rumble",
            "wikipedia.org",
            "twitter.com",
            "www.reddit.com",
            "stackoverflow.com",
            "www.quora.com",
        ]

        for item in mainstream:
            if dom.find(item) >= 0:
                return True

        if self.is_youtube():
            return True

        return False

    def is_youtube(self):
        dom = self.get_domain_only()
        if (
            dom.find("youtube.com") >= 0
            or dom.find("youtu.be") >= 0
            or dom.find("www.m.youtube") >= 0
        ):
            return True
        return False

    def download_all(self):
        from .programwrappers.wget import Wget

        wget = Wget(self.url)
        wget.download_all()
