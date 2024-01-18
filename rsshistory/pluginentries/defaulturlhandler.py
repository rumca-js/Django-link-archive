from ..webtools import Url, DefaultContentPage
from ..dateutils import DateUtils


class DefaultUrlHandler(DefaultContentPage):
    def __init__(self, url=None):
        super().__init__(url)
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

    def is_html(self, fast_check=True):
        if self.h is None:
            self.h = Url.get(self.url, fast_check=fast_check)
        return self.h.is_html(fast_check=fast_check)

    def is_rss(self, fast_check=True):
        if self.h is None:
            self.h = Url.get(self.url, fast_check=fast_check)
        return self.h.is_rss(fast_check=fast_check)

    def is_domain(self):
        if self.h is None:
            self.h = Url.get(self.url, fast_check=True)
        return self.h.is_domain()
