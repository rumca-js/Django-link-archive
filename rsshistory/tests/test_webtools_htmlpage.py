from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..webtools import HtmlPage


webpage_no_lang = """<html>
</html>
"""

webpage_lang_not_default = """<html lang="it">
</html>
"""

webpage_no_title = """<html>
</html>
"""

webpage_title_lower = """<html>
 <title>This is a lower case title</title>
</html>
"""

webpage_title_upper = """<html>
 <TITLE>This is a upper case title</TITLE>
</html>
"""

webpage_title_meta_og = """<html>
 <TITLE>selected meta title</TITLE>
 <meta property="og:title" content="selected og:title" />
</html>
"""

webpage_description_meta_og = """<html>
 <description>selected meta description</TITLE>
 <meta property="og:description" content="selected og:description" />
</html>
"""

webpage_links = """<html>
 <TITLE>This is a upper case title</TITLE>
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


class HtmlPageTest(TestCase):
    def test_default_language(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_no_lang)
        self.assertEqual(p.get_language(), "")

    def test_language_it(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_language(), "it")

    def test_no_title(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_no_title)

        # when page has no title, URL is chosen for the title
        self.assertEqual(p.get_title(), "http://test.com/my-site-test")

    def test_title_lowercase(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_lower)
        self.assertEqual(p.get_title(), "This is a lower case title")

    def test_title_uppercase(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_upper)
        self.assertEqual(p.get_title(), "This is a upper case title")

    def test_title_meta_og(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_meta_og)
        self.assertEqual(p.get_title(), "selected og:title")

    def test_description_meta_og(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_description_meta_og)
        self.assertEqual(p.get_description(), "selected og:description")

    def test_is_youtube(self):
        # default language
        p = HtmlPage("http://youtube.com/?v=1234", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = HtmlPage("http://youtu.be/djjdj", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = HtmlPage("http://www.m.youtube/?v=1235", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = HtmlPage("http://twitter.com/test", webpage_title_upper)
        self.assertFalse(p.is_youtube())

    def test_is_mainstream(self):
        # default language
        p = HtmlPage("http://youtube.com/?v=1234", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://youtu.be/djjdj", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://www.m.youtube/?v=1235", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://twitter.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://www.facebook.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://www.rumble.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://wikipedia.org/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

    def test_get_links(self):
        p = HtmlPage("http://mytestpage.com/?argument=value", webpage_links)

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

    def test_get_links_nodomain(self):
        p = HtmlPage("http://mytestpage.com/nodomain/", webpage_links)

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

    def test_get_rss_url(self):
        p = HtmlPage("http://mytestpage.com/nodomain/", webpage_rss_links)

        rss_url = p.get_rss_url()

        self.assertEqual("http://your-site.com/your-feed1.rss", rss_url)

    def test_get_rss_urls(self):
        p = HtmlPage("http://mytestpage.com/nodomain/", webpage_rss_links)

        all_rss = p.get_rss_urls()

        self.assertTrue("http://your-site.com/your-feed1.rss" in all_rss)
        self.assertTrue("http://your-site.com/your-feed2.rss" in all_rss)
        self.assertTrue("http://your-site.com/your-feed3.rss" in all_rss)