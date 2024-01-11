from ..webtools import Url
from ..dateutils import DateUtils


class DefaultUrlHandler(object):
    def __init__(self, url=None):
        self.url = url
        self.h = None

    def download_details(self):
        raise NotImplementedError

    def input2code(input_string):
        raise NotImplementedError

    def input2url(input_string):
        raise NotImplementedError

    def get_code(self):
        raise NotImplementedError

    def code2url(input_code):
        raise NotImplementedError

    def set_handler(self, handler=None):
        if handler:
            print("DefaultUrlHandler: passed from above")
            self.h = handler
        else:
            if self.h is None:
                print("DefaultUrlHandler: obtaining from url")
                self.h = Url.get(self.url)
                self.status_code = self.h.status_code

    def get_title(self):
        self.set_handler()
        return self.h.get_title()

    def get_published_date(self):
        return DateUtils.get_datetime_now_utc()

    def get_description(self):
        self.set_handler()
        return self.h.get_description()

    def get_language(self):
        self.set_handler()
        return self.h.get_language()

    def get_thumbnail(self):
        self.set_handler()
        return self.h.get_thumbnail()

    def get_author(self):
        self.set_handler()
        return self.h.get_author()

    def get_album(self):
        self.set_handler()
        return self.h.get_album()

    def get_tags(self):
        self.set_handler()
        return self.h.get_tags()

    def get_page_rating(self):
        self.set_handler()
        return self.h.get_page_rating()

    def get_properties(self):
        props = {}
        props["title"] = self.get_title()
        props["description"] = self.get_description()
        props["language"] = self.get_language()
        props["thumbnail"] = self.get_thumbnail()
        props["author"] = self.get_author()
        props["album"] = self.get_album()
        props["tags"] = self.get_tags()
        props["page_rating"] = self.get_page_rating()
        props["date_published"] = self.get_published_date()
        props["contents"] = self.get_contents()

        return props

    def get_contents(self):
        if self.h:
            return self.h.get_contents()

    def is_html(self, fast_check=True):
        url = Url.get(self.url, fast_check=fast_check)
        return url.is_html(fast_check=fast_check)

    def is_rss(self, fast_check=True):
        url = Url.get(self.url, fast_check=fast_check)
        return url.is_rss(fast_check=fast_check)

    def is_domain(self):
        url = Url.get(self.url)
        return url.is_domain()
