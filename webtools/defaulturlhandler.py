from .webtools import DefaultContentPage
from utils.dateutils import DateUtils


class DefaultUrlHandler(DefaultContentPage):
    """
    Default URL handler.
    Behavior can be changed by setting .h handler property
    """

    def __init__(self, url=None, contents=None):
        super().__init__(
            url,
            contents=contents,
        )
        self.h = None
        self.response = None
        self.dead = None
        self.code = None  # social media handle, ID of channel, etc.

    def is_handled_by(self):
        return True

    def get_url(self):
        if self.code:
            return code2url(self.code)

    def get_feed_url(self):
        """
        even for post, or individual videos we might request feed url
        """
        if self.code:
            return self.code2feed(self.code)

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


class DefaultChannelHandler(DefaultContentPage):

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

        feed_url = self.get_feed_url()
        if not feed_url:
            AppLogging.error(
                "Url:{} Cannot read feed URL".format(self.url)
            )
            self.dead = True
            return

        options = Url.get_url_options(feed_url)
        u = Url(feed_url, page_options=options, handler_class=HttpPageHandler)
        self.response = u.get_response()

        if (
            not self.response
            or not self.response.is_valid()
        ):
            self.dead = True

        if self.response:
            self.contents = self.response.get_text()
            self.process_contents()

            return self.response
