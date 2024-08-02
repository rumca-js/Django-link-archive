from .webtools import DefaultContentPage
from ..dateutils import DateUtils


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

    def input2code(input_string):
        raise NotImplementedError

    def input2url(input_string):
        raise NotImplementedError

    def get_code(self):
        raise NotImplementedError

    def code2url(input_code):
        raise NotImplementedError

    def get_url(self):
        return self.code2url(self.code)
