from ..webtools import Url
from ..dateutils import DateUtils


class DefaultUrlHandler(object):
    def __init__(self, url=None):
        self.url = url
        self.h = None

    def set_handler(self):
        if self.h is None:
            self.h = Url.get(self.url)

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

        return props
