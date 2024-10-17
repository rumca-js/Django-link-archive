from .pages import DefaultContentPage
from utils.dateutils import DateUtils


class DefaultUrlHandler(DefaultContentPage):
    """
    Default URL handler.
    Behavior can be changed by setting .h handler property
    """

    def __init__(self, url=None, contents=None, page_options=None):
        super().__init__(
            url,
            contents=contents,
        )
        self.h = None
        self.response = None
        self.dead = None
        self.code = None  # social media handle, ID of channel, etc.
        self.options = page_options
        self.handler = None # one handler to rule them all

    def is_handled_by(self):
        return True

    def get_url(self):
        if self.code:
            return self.code2url(self.code)
        else:
            return self.url

    def get_feeds(self):
        """
        even for post, or individual videos we might request feed url
        """
        if self.code:
            return [self.code2feed(self.code)]
        return []

    def input2code(self, input_string):
        raise NotImplementedError

    def input2url(self, input_string):
        raise NotImplementedError

    def get_code(self):
        raise NotImplementedError

    def code2url(self, input_code):
        raise NotImplementedError

    def code2feed(self, code):
        raise NotImplementedError

    def get_name(self):
        raise NotImplementedError

    def get_contents(self):
        if self.response:
            return self.response.get_text()

    def get_title(self):
        if self.handler:
            return self.handler.get_title()

    def get_description(self):
        if self.handler:
            return self.handler.get_description()

    def get_language(self):
        if self.handler:
            return self.handler.get_language()

    def get_thumbnail(self):
        if self.handler:
            return self.handler.get_thumbnail()

    def get_author(self):
        if self.handler:
            return self.handler.get_author()

    def get_album(self):
        if self.handler:
            return self.handler.get_album()

    def get_tags(self):
        if self.handler:
            return self.handler.get_tags()

    def get_date_published(self):
        if self.handler:
            return self.handler.get_date_published()

    def get_status_code(self):
        if self.response:
            return self.response.get_status_code()

        return 0

    def get_entries(self):
        return []

    def get_response(self):
        """
        By default we use HTML response
        """
        from .url import Url
        from .handlerhttppage import HttpPageHandler

        if self.response:
            return self.response

        # now call url with those options
        self.handler = Url(self.url, handler_class=HttpPageHandler)
        self.response = self.handler.get_response()

        if not self.response or not self.response.is_valid():
            self.dead = True

        if self.response:
            self.contents = self.response.get_text()

            return self.response


class DefaultChannelHandler(DefaultUrlHandler):
    def get_contents(self):
        """
        We obtain information about channel.
        We cannot use HTML page to obtain thumbnail - as web page asks to log in to view this
        """
        if self.dead:
            return

        if self.contents:
            return self.contents

        response = self.get_response()
        if response:
            return self.response.get_text()

    def get_response(self):
        """
        By default we use HTML response
        """
        from .url import Url
        from .handlerhttppage import HttpPageHandler

        if self.response:
            return self.response

        feeds = self.get_feeds()
        if not feeds or len(feeds) == 0:
            self.dead = True
            return

        feed_url = feeds[0]

        # now call url with those options
        self.handler = Url(feed_url, handler_class=HttpPageHandler)
        self.response = self.handler.get_response()

        if not self.response or not self.response.is_valid():
            self.dead = True

        if self.response:
            self.contents = self.response.get_text()

            return self.response
