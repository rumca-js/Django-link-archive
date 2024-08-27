from utils.dateutils import DateUtils


class InternetArchiveInterface(object):
    def __init__(self, url):
        self.url = url

    def get_archive_url(self):
        pass


class InternetArchive(InternetArchiveInterface):
    def __init__(self, url):
        super().__init__(url)

    def get_archive_url(self, time=None):
        if not time:
            time = DateUtils.get_datetime_now_utc()

        if time:
            time_str = time.strftime("%Y%m%d")
            return "https://web.archive.org/web/{}110000*/".format(time_str) + self.url


class InternetArchiveBuilder(object):
    def get(url):
        return InternetArchive(url)
