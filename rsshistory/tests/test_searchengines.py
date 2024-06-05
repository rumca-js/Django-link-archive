from ..webtools import Url, PageOptions, HtmlPage, PageResponseObject
from ..controllers import SearchEngines, SearchEngineGoogle,SearchEngineGoogleCache

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SearchEnginesTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_search_engine_google(self):
        s = SearchEngineGoogle("test")

        self.assertEqual(s.get_search_string(), "https://google.com/search?q=test")

    def test_search_engine_google_cache(self):
        url = "https://lifehacker.com/how-to-access"

        s = SearchEngineGoogleCache(url)

        self.assertEqual(s.get_search_string(), "http://webcache.googleusercontent.com/search?q=cache:https%3A//lifehacker.com/how-to-access")
