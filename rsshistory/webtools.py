import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse
import html
import traceback
import requests
import re


class Page(object):
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"

    def __init__(self, url, contents=None):
        self.url = url
        self.contents = contents

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

    def get_contents(self):
        if self.contents:
            return self.contents

        hdr = {
            "User-Agent": Page.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }

        try:
            r = requests.get(self.url, headers=hdr)
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

        whlang = self.contents.find("lang")
        if whlang >= 0:
            lang = self.extract_html(self.contents, '"', '"', whlang)
            if not lang:
                return "en"

            if len(lang) > 5:
                return "en"

            if lang.find("<") >= 0:
                return "en"

            return lang
        else:
            return "en"

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

        wh1 = self.contents.find("<title", 0)
        if wh1 == -1:
            wh1 = self.contents.find("<TITLE", 0)

        if wh1 == -1:
            return None

        wh1a = self.contents.find(">", wh1)
        wh2 = self.contents.find("</", wh1a + 1)

        title = self.contents[wh1a + 1 : wh2].strip()
        title = html.unescape(title)

        return title

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
