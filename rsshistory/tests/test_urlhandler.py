from ..pluginurl.urlhandler import UrlHandler
from ..pluginurl.handlervideoyoutube import YouTubeVideoHandler
from ..webtools import RssPage, HtmlPage

from .fakeinternet import FakeInternetTestCase


class UrlHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_rss(self):
        handler = UrlHandler("https://rsspage.com/rss.xml")

        self.assertTrue(handler.is_valid())
        self.assertEqual(type(handler.p), RssPage)

    def test_get_html(self):
        handler = UrlHandler("https://linkedin.com")

        self.assertTrue(handler.is_valid())
        self.assertEqual(type(handler.p), HtmlPage)

    def test_get_youtube_video(self):
        handler = UrlHandler("https://www.youtube.com/watch?v=1234")

        self.assertEqual(type(handler.p), UrlHandler.youtube_video_handler)

    def test_get_youtube_channel(self):
        handler = UrlHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        self.assertEqual(type(handler.p), UrlHandler.youtube_channel_handler)

    def test_rss_get_properties(self):
        handler = UrlHandler("https://simple-rss-page.com/rss.xml")

        props = handler.get_properties()

        self.assertEqual(props["title"], "Simple title")
        self.assertEqual(props["description"], "Simple description")

    def test_html_get_properties(self):
        handler = UrlHandler("https://linkedin.com")

        props = handler.get_properties()

        self.assertEqual(props["title"], "LinkedIn Page title")
        self.assertEqual(props["description"], "LinkedIn Page description")

    def test_youtube_channel_get_properties(self):
        handler = UrlHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        props = handler.p.get_properties()

        self.assertEqual(props["title"], "SAMTIME on Odysee")

    def test_youtube_channel_get_title(self):
        handler = UrlHandler(
            "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        )

        self.assertEqual(handler.p.get_title(), "SAMTIME on Odysee")

    def test_get_spotify(self):
        handler = UrlHandler("https://open.spotify.com/somebody/episodes")

        self.assertEqual(type(handler.p), HtmlPage)

        self.assertTrue(handler.options.use_selenium_headless)

    def test_get_warhammer_community(self):
        handler = UrlHandler("https://www.warhammer-community.com")

        self.assertEqual(type(handler.p), HtmlPage)

        self.assertTrue(handler.options.use_selenium_full)

    def test_get__defcon_org(self):
        handler = UrlHandler("https://defcon.org")

        self.assertEqual(type(handler.p), HtmlPage)

        self.assertTrue(handler.options.use_selenium_full)

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
