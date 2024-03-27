from ..webtools import HtmlPage, BasePage, calculate_hash

from .fakeinternet import FakeInternetTestCase, MockRequestCounter

webpage_no_lang = """<html>
    <body>
    </body>
</html>
"""

webpage_lang_not_default = """<html lang="it">
    <body>
    </body>
</html>
"""

webpage_no_title = """<html>
    <body>
    </body>
</html>
"""

webpage_title_lower = """<html>
 <title>This is a lower case title</title>
    <body>
    </body>
</html>
"""

webpage_title_upper = """<html>
 <TITLE>This is a upper case title</TITLE>
    <body>
    </body>
</html>
"""

webpage_title_head = """<html>
 <title>selected title</title>
    <body>
    </body>
</html>
"""

webpage_title_meta = """<html>
 <meta name="title" content="selected meta title" />
    <body>
    </body>
</html>
"""

webpage_title_meta_og = """<html>
 <TITLE>selected meta title</TITLE>
 <meta property="og:title" content="selected og:title" />
    <body>
    </body>
</html>
"""

webpage_description_head = """<html>
 <description>selected description</description>
    <body>
    </body>
</html>
"""

webpage_description_meta = """<html>
 <meta name="description" content="selected meta description"/>
    <body>
    </body>
</html>
"""

webpage_description_meta_og = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
    <body>
    </body>
</html>
"""

webpage_meta_article_date = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
 <meta property="article:published_time" content="2024-01-09T21:26:00Z" />
    <body>
    </body>
</html>
"""

webpage_meta_music_release_date = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
 <meta name="music:release_date" content="2024-01-09T21:26:00Z"/>
    <body>
    </body>
</html>
"""

webpage_meta_youtube_publish_date = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
 <meta itemprop="datePublished" content="2024-01-11T09:00:07-00:00">
 <meta itemprop="uploadDate" content="2024-01-11T09:00:07-00:00">
 <meta itemprop="genre" content="Science &amp; Technology">
    <body>
    </body>
</html>
"""


webpage_links = """<html>
 <TITLE>This is a upper case title</TITLE>
    <body>
 <a custom-peroperty="custom-property-value" href="http://otherpage1.net" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="https://otherpage2.net" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test1" class="contentLink  hero--img -first">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test2.html" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test3.htm" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test4.js" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test5/" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="//test6.domain.com/" class="class">
   <picture></picture>
   </a>
    </body>
</html>
"""

webpage_rss_links = """<html>
 <head>
 <TITLE>This is a upper case title</TITLE>
 <link rel="alternate" type="application/rss+xml" title="9to5Google &raquo; Feed" href="http://your-site.com/your-feed1.rss" />
 <link rel="alternate" type="application/rss+xml" title="9to5Google &raquo; Feed" href="http://your-site.com/your-feed2.rss" />
 <link rel="alternate" type="application/rss+xml" title="9to5Google &raquo; Feed" href="http://your-site.com/your-feed3.rss" />

 </head>
 <body>
 page body
 </body>
"""

webpage_html_favicon = """<html>
 <head>
 <link rel="shortcut icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico" type="image/x-icon"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_32x32.png" sizes="32x32"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_48x48.png" sizes="48x48"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_96x96.png" sizes="96x96"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_144x144.png" sizes="144x144">
 <title>YouTube</title>

 </head>
 <body>
 page body
 </body>
"""

webpage_html_encoded_links = """<html>
 <head>
 <link rel="shortcut icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico" type="image/x-icon"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_32x32.png" sizes="32x32"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_48x48.png" sizes="48x48"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_96x96.png" sizes="96x96"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_144x144.png" sizes="144x144">
 <title>YouTube</title>

 </head>
 <body>
     <a href="https:&#x2F;&#x2F;github.com&#x2F;pyFFTW&#x2F;pyFFTW">https:&#x2F;&#x2F;github.com&#x2F;pyFFTW&#x2F;pyFFTW</a>
     <a href="http:&#x2F;&#x2F;github-help-wanted.com" rel="nofollow">http:&#x2F;&#x2F;github-help-wanted.com</a>
 </body>
"""

webpage_html_meta_charset = """<html>
 <head>
   <link rel="shortcut icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico" type="image/x-icon"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_32x32.png" sizes="32x32"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_48x48.png" sizes="48x48"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_96x96.png" sizes="96x96"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_144x144.png" sizes="144x144">
   <title>YouTube</title>
   <meta charset="shift_jis" />
 </head>
 <body>
     test
 </body>
"""
webpage_html_meta_http_equiv_charset = """<html>
 <head>
   <link rel="shortcut icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico" type="image/x-icon"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_32x32.png" sizes="32x32"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_48x48.png" sizes="48x48"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_96x96.png" sizes="96x96"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_144x144.png" sizes="144x144">
   <title>YouTube</title>
   <meta http-equiv="Content-Type" content = "text/html; charset=shift_jis" />
 </head>
 <body>
     test
 </body>
"""


class HtmlPageTest(FakeInternetTestCase):
    def test_default_language(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_no_lang)
        self.assertEqual(p.get_language(), "")
        self.assertTrue(p.is_valid())

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_language_it(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_lang_not_default)
        self.assertEqual(p.get_language(), "it")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_no_title(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_no_title)

        # when page has no title, URL is chosen for the title
        self.assertEqual(p.get_title(), None)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_title_lowercase(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_title_lower)
        self.assertEqual(p.get_title(), "This is a lower case title")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_title_uppercase(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_title_upper)
        self.assertEqual(p.get_title(), "This is a upper case title")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_title_head(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_title_head)
        self.assertEqual(p.get_title(), "selected title")
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_title_meta(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_title_meta)
        self.assertEqual(p.get_title(), "selected meta title")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_title_meta_og(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_title_meta_og)
        self.assertEqual(p.get_title(), "selected og:title")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_description_head(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_description_head)
        self.assertEqual(p.get_description(), "selected description")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_description_meta(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_description_meta)
        self.assertEqual(p.get_description(), "selected meta description")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_description_meta_og(self):
        MockRequestCounter.mock_page_requests = 0

        # default language
        p = HtmlPage("https://linkedin.com/test", webpage_description_meta_og)
        self.assertEqual(p.get_description(), "selected og:description")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_links(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage("http://mytestpage.com/test", webpage_links)

        links = p.get_links()

        self.assertTrue("http://otherpage1.net" in links)
        self.assertTrue("https://otherpage2.net" in links)

        self.assertTrue("http://mytestpage.com/test/test1" in links)
        self.assertTrue("http://mytestpage.com/test/test2.html" in links)
        self.assertTrue("http://mytestpage.com/test/test3.htm" in links)
        # java script is not accepted by default
        self.assertTrue("http://mytestpage.com/test/test4.js" not in links)
        self.assertTrue("http://mytestpage.com/test/test5/" in links)
        self.assertTrue("https://test6.domain.com/" in links)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_links_nodomain(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage("http://mytestpage.com/test", webpage_links)

        links = p.get_links()

        self.assertTrue("http://otherpage1.net" in links)
        self.assertTrue("https://otherpage2.net" in links)

        self.assertTrue("http://mytestpage.com/test/test1" in links)
        self.assertTrue("http://mytestpage.com/test/test2.html" in links)
        self.assertTrue("http://mytestpage.com/test/test3.htm" in links)
        # java script is not accepted by default
        self.assertTrue("http://mytestpage.com/test/test4.js" not in links)
        self.assertTrue("http://mytestpage.com/test/test5/" in links)
        self.assertTrue("https://test6.domain.com/" in links)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_rss_url(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage("https://linkedin.com/test", webpage_rss_links)

        rss_url = p.get_rss_url()

        self.assertEqual("http://your-site.com/your-feed1.rss", rss_url)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_rss_urls(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage("https://linkedin.com/test", webpage_rss_links)

        all_rss = p.get_rss_urls()

        self.assertTrue("http://your-site.com/your-feed1.rss" in all_rss)
        self.assertTrue("http://your-site.com/your-feed2.rss" in all_rss)
        self.assertTrue("http://your-site.com/your-feed3.rss" in all_rss)

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_favicons(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage("https://linkedin.com/test", webpage_html_favicon)

        all_favicons = p.get_favicons()

        self.assertEqual(
            all_favicons[0][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico",
        )
        self.assertEqual(
            all_favicons[1][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_32x32.png",
        )
        self.assertEqual(
            all_favicons[2][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_48x48.png",
        )
        self.assertEqual(
            all_favicons[3][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_96x96.png",
        )
        self.assertEqual(
            all_favicons[4][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_144x144.png",
        )
        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_date_published_article_date(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage(
            "https://linkedin.com/test",
            webpage_meta_article_date,
        )

        date = p.get_date_published()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-09T21:26:00+00:00")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_date_published_music_date(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage(
            "https://linkedin.com/test",
            webpage_meta_music_release_date,
        )

        date = p.get_date_published()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-09T21:26:00+00:00")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_date_published_youtube(self):
        MockRequestCounter.mock_page_requests = 0

        p = HtmlPage(
            "https://linkedin.com/test",
            webpage_meta_youtube_publish_date,
        )

        date = p.get_date_published()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-11T09:00:07+00:00")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_body_hash(self):
        MockRequestCounter.mock_page_requests = 0

        reader = HtmlPage(
            "https://linkedin.com/test", webpage_meta_youtube_publish_date
        )
        hash = reader.get_body_hash()
        bodytext = str(reader.get_body_text())

        self.assertTrue(bodytext)
        self.assertTrue(bodytext != "")

        self.assertEqual(hash, calculate_hash(bodytext))

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_links_encoded(self):
        MockRequestCounter.mock_page_requests = 0

        reader = HtmlPage("https://linkedin.com/test", webpage_html_encoded_links)
        links = sorted(list(reader.get_links()))

        self.assertEqual(links[0], "http://github-help-wanted.com")
        self.assertEqual(links[1], "https://github.com/pyFFTW/pyFFTW")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_meta_charset(self):
        MockRequestCounter.mock_page_requests = 0

        reader = HtmlPage("https://linkedin.com/test", webpage_html_meta_charset)
        self.assertEqual(reader.get_charset(), "shift_jis")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)

    def test_get_meta_http_equiv_charset(self):
        MockRequestCounter.mock_page_requests = 0

        reader = HtmlPage(
            "https://linkedin.com/test", webpage_html_meta_http_equiv_charset
        )
        self.assertEqual(reader.get_charset(), "shift_jis")

        self.assertEqual(MockRequestCounter.mock_page_requests, 0)
