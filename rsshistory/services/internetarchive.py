

class InternetArchiveInterface(object):
    def __init__(self, url):
        self.url = url

    def get_archive_url(self):
        pass


class InternetArchive(InternetArchiveInterface):
    def __init__(self, url):
        super().__init__(url)

    def get_archive_url(self):
        """
        TODO what to do with date? obtain from entry? current time stamp?
        """
        return "https://web.archive.org/web/20240508000000*/" + self.url


class InternetArchiveBuilder(object):
    def get():
        pass
