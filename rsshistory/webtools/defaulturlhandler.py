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

    def is_handled_by(self):
        return True

    def get_url(self):
        if self.code:
            return code2url(self.code)

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
        from .url import Url

        if self.response:
            return self.response

        feeds = self.get_feeds()
        if not feeds or len(feeds) == 0:
            AppLogging.error("Url:{} Cannot read feed URL".format(self.url))
            self.dead = True
            return

        feed_url = feeds[0]

        options = self.get_options(feed_url)

        # now call url with those options
        url = Url(feed_url, page_options=options, handler_class=HttpPageHandler)
        self.response = url.get_response()

        if not self.response or not self.response.is_valid():
            self.dead = True

        if self.response:
            self.contents = self.response.get_text()
            self.process_contents()

            return self.response

    def get_options(self, feed_url):
        url = Url(feed_url)
        options = url.page_options

        if self.options:
            options.copy_config(self.options)

        return options
