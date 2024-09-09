from utils.services import InternetArchive
from datetime import datetime

from .fakeinternet import FakeInternetTestCase


class InternetArchiveTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_translate(self):
        p = InternetArchive("https://www-youtube.com/test?parameter=True")

        date_str = "2024-05-12"
        date_input = datetime.strptime(date_str, "%Y-%m-%d")

        # call tested function
        url = p.get_archive_url(date_input)

        self.assertEqual(
            url,
            "https://web.archive.org/web/20240512110000*/https://www-youtube.com/test?parameter=True",
        )
