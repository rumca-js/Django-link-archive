from ..webtools import Url, DefaultContentPage
from ..dateutils import DateUtils


class DefaultUrlHandler(DefaultContentPage):
    """
    Default URL handler.
    Behavior can be changed by setting .h handler property
    """

    def __init__(self, url=None, contents=None, page_object=None, options=None):
        super().__init__(
            url, contents=contents, page_object=page_object, options=options
        )
        self.h = None

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
