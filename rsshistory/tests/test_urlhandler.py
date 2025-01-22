from ..models import Browser

from ..webtools import (
   RssPage,
   HtmlPage,
   HttpPageHandler,
   YouTubeVideoHandler,
   ScriptCrawler,
   SeleniumChromeFull,
)

from ..pluginurl.urlhandler import UrlHandlerEx, UrlHandler

from .fakeinternet import FakeInternetTestCase


class UrlHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_rss(self):
        handler = UrlHandler("https://rsspage.com/rss.xml")
        handler.get_response()

        self.assertTrue(handler.is_valid())
        self.assertEqual(type(handler.get_handler()), HttpPageHandler)
        self.assertEqual(type(handler.get_handler().p), RssPage)

    def test_get_html(self):
        handler = UrlHandler("https://linkedin.com")
        handler.get_response()

        self.assertTrue(handler.is_valid())
        self.assertEqual(type(handler.get_handler()), HttpPageHandler)
        self.assertEqual(type(handler.get_handler().p), HtmlPage)

    def test_get_youtube_video(self):
        handler = UrlHandler("https://www.youtube.com/watch?v=1234")

        self.assertEqual(type(handler.get_handler()), UrlHandlerEx.youtube_video_handler)

    def test_get_youtube_channel(self):
        handler = UrlHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        self.assertEqual(
            type(handler.get_handler()), UrlHandlerEx.youtube_channel_handler
        )

    def test_rss_get_properties(self):
        handler = UrlHandler("https://simple-rss-page.com/rss.xml")
        handler.get_response()
        props = handler.get_properties()

        self.assertEqual(props["title"], "Simple title")
        self.assertEqual(props["description"], "Simple description")

    def test_html_get_properties(self):
        handler = UrlHandler("https://linkedin.com")
        handler.get_response()

        props = handler.get_properties()

        self.assertEqual(props["title"], "Https LinkedIn Page title")
        self.assertEqual(props["description"], "LinkedIn Page description")

    def test_youtube_channel_get_properties(self):
        handler = UrlHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        handler.get_response()

        props = handler.get_properties()
        print(props)

        self.assertEqual(props["title"], "SAMTIME on YouTube")

    def test_youtube_channel_get_title(self):
        handler = UrlHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )
        handler.get_response()

        self.assertEqual(handler.get_title(), "SAMTIME on YouTube")

    def test_get_cleaned_link_stupid_google_link(self):
        cleaned_link = UrlHandler.get_cleaned_link(
            "https://www.google.com/url?q=https://forum.ddopl.com/&sa=Udupa"
        )

        self.assertEqual(cleaned_link, "https://forum.ddopl.com")

    def test_get_cleaned_link_stupid_google_link2(self):
        cleaned_link = UrlHandler.get_cleaned_link(
            "https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://worldofwarcraft.blizzard.com/&ved=2ahUKEwjtx56Pn5WFAxU2DhAIHYR1CckQFnoECCkQAQ&usg=AOvVaw1pDkx5K7B5loKccvg_079-"
        )

        self.assertEqual(cleaned_link, "https://worldofwarcraft.blizzard.com")

    def test_get_cleaned_link_stupid_youtube_link(self):
        cleaned_link = UrlHandler.get_cleaned_link(
            "https://www.youtube.com/redirect?event=lorum&redir_token=ipsum&q=https%3A%2F%2Fcorridordigital.com%2F&v=LeB9DcFT810"
        )

        self.assertEqual(cleaned_link, "https://corridordigital.com/&v=LeB9DcFT810")

    def test_get_cleaned_link(self):
        cleaned_link = UrlHandler.get_cleaned_link("https://www.YouTube.com/Test")
        self.assertEqual(cleaned_link, "https://www.youtube.com/Test")

        cleaned_link = UrlHandler.get_cleaned_link("https://www.YouTube.com/Test/")
        self.assertEqual(cleaned_link, "https://www.youtube.com/Test")


class UrlHandlerExTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_rss(self):
        handler = UrlHandlerEx("https://rsspage.com/rss.xml")
        properties = handler.get_properties()

        self.assertTrue(properties)

    def test_get_options(self):
        Browser.objects.all().delete()

        browser1 = Browser.objects.create(
                name = "test1",
                crawler = "RequestsCrawler",
                settings = '{"test_setting" : "something"}',
        )

        browser2 = Browser.objects.create(
                name = "test2",
                crawler = "RequestsCrawler",
                settings = '{"test_setting" : "something"}',
        )

        setup1 = browser1.get_setup()
        setup2 = browser2.get_setup()

        test_link = "https://rsspage.com/rss.xml"

        options = UrlHandlerEx.get_options(test_link)

        options.mode_mapping = [setup1, setup2]

        handler = UrlHandlerEx(test_link, page_options=options)
        properties = handler.get_properties()

        self.assertTrue(properties)
