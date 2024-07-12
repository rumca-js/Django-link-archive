"""
This module provides replacement for the Internet.

 - when test make requests to obtain a page, we return artificial data here
 - when there is a request to obtain youtube JSON data, we provide artificial data, etc.
"""
import logging
from django.test import TestCase
from django.contrib.auth.models import User

# import chardet

from ..models import AppLogging, ConfigurationEntry
from ..dateutils import DateUtils
from ..webtools import RequestBuilder, PageResponseObject
from ..configuration import Configuration

from ..pluginurl.urlhandler import UrlHandler
from ..pluginurl.handlervideoyoutube import YouTubeVideoHandler, YouTubeJsonHandler
from ..pluginurl.handlerchannelyoutube import YouTubeChannelHandler


from .fakeinternetdata import (
    webpage_with_real_rss_links,
    webpage_simple_rss_page,
    webpage_old_pubdate_rss,
    webpage_no_pubdate_rss,
    webpage_html_favicon,
    webpage_with_rss_link_rss_contents,
    webpage_html_casinos,
)
from .fake.youtube import (
    youtube_robots_txt,
    youtube_sitemap_sitemaps,
    youtube_sitemap_product,
    webpage_youtube_airpano_feed,
    webpage_samtime_youtube_rss,
)
from .fake.robotstxtcom import (
    robots_txt_example_com_robots,
)
from .fake.codeproject import (
    webpage_code_project_rss,
)
from .fake.hackernews import (
    webpage_hackernews_rss,
)
from .fake.warhammercommunity import (
    warhammer_community_rss,
)
from .fake.instance import (
    instance_entries_json,
    instance_sources_json_empty,
    instance_entries_json_empty,
    instance_entries_source_100_json,
    instance_source_100_url,
    instance_source_100_json,
    instance_source_101_json,
    instance_source_102_json,
    instance_source_103_json,
    instance_source_104_json,
    instance_source_105_json,
    instance_sources_page_1,
    instance_sources_page_2,
)


class PageBuilder(object):
    def __init__(self):
        self.charset = "UTF-8"
        self.title = None
        self.title_meta = None
        self.description_meta = None
        self.author = None
        self.keywords = None
        self.og_title = None
        self.og_description = None
        self.body_text = ""

    def build_contents(self):
        html = self.build_html()
        html = self.build_head(html)
        html = self.build_body(html)
        return html

    def build_html(self):
        return """
        <html>
        ${HEAD}
        ${BODY}
        </html>"""

    def build_body(self, html):
        html = html.replace("${BODY}", "<body>{}</body>".format(self.body_text))
        return html

    def build_head(self, html):
        # fmt: off

        meta_info = ""
        if self.title:
            meta_info += '<title>{}</title>\n'.format(self.title)
        if self.title_meta:
            meta_info += '<meta name="title" content="{}">\n'.format(self.title_meta)
        if self.description_meta:
            meta_info += '<meta name="description" content="{}">\n'.format(self.description_meta)
        if self.author:
            meta_info += '<meta name="author" content="{}">\n'.format(self.author)
        if self.keywords:
            meta_info += '<meta name="keywords" content="{}">\n'.format(self.keywords)
        if self.og_title:
            meta_info += '<meta property=”og:title” content="{}">\n'.format(self.og_title)
        if self.og_description:
            meta_info += '<meta property=”og:description” content="{}">\n'.format(self.og_description)

        # fmt: on

        html = html.replace("${HEAD}", "<head>{}</head>".format(meta_info))
        return html


class MockRequestCounter(object):
    mock_page_requests = 0


class YouTubeJsonHandlerMock(YouTubeJsonHandler):
    def __init__(self, url):
        super().__init__(url)

    def download_details_youtube(self):
        print("Mocked YouTube request URL: {}".format(self.url))
        MockRequestCounter.mock_page_requests += 1

        if self.get_video_code() == "1234":
            self.yt_text = """{"_filename" : "1234 test file name",
            "title" : "1234 test title",
            "description" : "1234 test description",
            "channel_url" : "https://youtube.com/channel/1234-channel",
            "channel" : "1234-channel",
            "id" : "1234-id",
            "channel_id" : "1234-channel-id",
            "thumbnail" : "https://youtube.com/files/1234-thumbnail.png",
            "upload_date" : "20231113",
            "live_status" : "False"
            }"""
            return True
        if self.get_video_code() == "666":
            return False
        if self.get_video_code() == "555555":
            self.yt_text = """{"_filename" : "555555 live video.txt",
            "title" : "555555 live video",
            "description" : "555555 live video description",
            "channel_url" : "https://youtube.com/channel/test.txt",
            "channel" : "JoYoe",
            "id" : "3433",
            "channel_id" : "JoYoe",
            "thumbnail" : "https://youtube.com/files/whatever.png",
            "upload_date" : "20231113",
            "live_status" : "True"
            }"""
        else:
            self.yt_text = """{"_filename" : "test.txt",
            "title" : "test.txt",
            "description" : "test.txt",
            "channel_url" : "https://youtube.com/channel/test.txt",
            "channel" : "JoYoe",
            "id" : "3433",
            "channel_id" : "JoYoe",
            "thumbnail" : "https://youtube.com/files/whatever.png",
            "upload_date" : "20231113",
            "live_status" : "False"
            }"""
        return True

    def download_details_return_dislike(self):
        self.rd_text = """{}"""
        return True


class YouTubeChannelHandlerMock(YouTubeChannelHandler):
    def __init__(self, url=None):
        super().__init__(url)

    def get_contents(self):
        if self.dead:
            return


class DjangoRequestObject(object):
    def __init__(self, user):
        self.user = user


class TestResponseObject(PageResponseObject):
    """
    TODO maybe we should inherit from webtools/PageResponseObject?
    """

    def __init__(self, url, headers, timeout):
        self.status_code = 200

        contents = self.get_contents_for_url(url)

        self.url = url
        self.text = contents
        self.content = contents
        self.headers = {}

        # encoding = chardet.detect(contents)['encoding']
        encoding = "utf-8"
        self.apparent_encoding = encoding
        self.encoding = encoding

        self.set_headers(url)
        self.set_status(url)

    def set_headers(self, url):
        if url == "https://page-with-last-modified-header.com":
            self.headers["Last-Modified"] = "Wed, 03 Apr 2024 09:39:30 GMT"

    def set_status(self, url):
        if url.startswith("https://www.youtube.com/watch?v=666"):
            self.status_code = 500

        elif url == "https://invalid.rsspage.com/rss.xml":
            self.status_code = 500

        elif url == "https://page-with-http-status-500.com":
            self.status_code = 500

        elif url == "https://page-with-http-status-400.com":
            self.status_code = 400

        elif url == "https://page-with-http-status-300.com":
            self.status_code = 300

        elif url == "https://page-with-http-status-200.com":
            self.status_code = 200

        elif url == "https://page-with-http-status-100.com":
            self.status_code = 100

        elif url == "http://page-with-http-status-500.com":
            self.status_code = 500

        elif url == "http://page-with-http-status-400.com":
            self.status_code = 400

        elif url == "http://page-with-http-status-300.com":
            self.status_code = 300

        elif url == "http://page-with-http-status-200.com":
            self.status_code = 200

        elif url == "http://page-with-http-status-100.com":
            self.status_code = 100

        elif url == "https://page-with-https-status-200-http-status-500.com":
            self.status_code = 200

        elif url == "http://page-with-https-status-200-http-status-500.com":
            self.status_code = 500

        elif url == "https://page-with-https-status-500-http-status-200.com":
            self.status_code = 500

        elif url == "http://page-with-https-status-500-http-status-200.com":
            self.status_code = 200

    def get_contents_for_url(self, url):
        if url.startswith("https://youtube.com/channel/"):
            return self.get_contents_youtube_channel(url)

        if url.startswith("https://www.youtube.com/watch?v=666"):
            return webpage_no_pubdate_rss

        if url.startswith("https://www.youtube.com/feeds"):
            return webpage_samtime_youtube_rss

        if url == "https://www.youtube.com/robots.txt":
            return youtube_robots_txt

        if url == "https://www.youtube.com/sitemaps/sitemap.xml":
            return youtube_sitemap_sitemaps

        if url == "https://www.youtube.com/product/sitemap.xml":
            return youtube_sitemap_product

        if url.startswith("https://hnrss.org"):
            return webpage_hackernews_rss

        if url.startswith("https://news.ycombinator.com/item?id=39940707"):
            return webpage_samtime_youtube_rss

        if url.startswith("https://warhammer-community.com/feed"):
            return warhammer_community_rss

        if url.startswith("https://isocpp.org/blog/rss/category/news"):
            return webpage_samtime_youtube_rss

        if url.startswith("https://cppcast.com/feed.rss"):
            return webpage_samtime_youtube_rss

        elif url == "https://multiple-favicons/page.html":
            return webpage_html_favicon

        elif url == "https://rsspage.com/rss.xml":
            return webpage_samtime_youtube_rss

        elif url == "https://invalid.rsspage.com/rss.xml":
            return ""

        elif url == "https://simple-rss-page.com/rss.xml":
            return webpage_simple_rss_page

        elif url == "https://empty-page.com":
            return ""

        elif url == "https://www.codeproject.com/WebServices/NewsRSS.aspx":
            return webpage_code_project_rss

        elif url == "https://page-with-two-links.com":
            b = PageBuilder()
            b.title_meta = "Page title"
            b.description_meta = "Page description"
            b.og_title = "Page og_title"
            b.og_description = "Page og_description"
            b.body_text = """<a href="https://link1.com">Link1</a>
                     <a href="https://link2.com">Link2</a>"""

            return b.build_contents()

        elif url == "https://page-with-rss-link.com":
            return """
              <html>
                 <head>
                     <link type="application/rss+xml"  href="https://page-with-rss-link.com/feed"/>
                 </head>
                 <body>
                    no body
                 </body>
             </html>
             """

        elif url == "https://page-with-rss-link.com/feed":
            return webpage_with_rss_link_rss_contents

        elif url == "https://slot-casino-page.com":
            return webpage_html_casinos

        elif url == "https://page-with-real-rss-link.com":
            return webpage_with_real_rss_links

        elif url.startswith("https://instance.com/apps/rsshistory"):
            return self.get_contents_instance(url)

        elif url == "https://title-in-head.com":
            b = PageBuilder()
            b.title = "Page title"
            b.description_meta = "Page description"
            b.og_description = "Page og_description"
            b.body_text = """Something in the way"""
            return b.build_contents()

        elif url == "https://title-in-meta.com":
            b = PageBuilder()
            b.title = "Page title"
            b.description_meta = "Page description"
            b.og_description = "Page og_description"
            b.body_text = """Something in the way"""
            return b.build_contents()

        elif url == "https://title-in-og.com":
            b = PageBuilder()
            b.og_title = "Page title"
            b.description_meta = "Page description"
            b.og_description = "Page og_description"
            b.body_text = """Something in the way"""
            return b.build_contents()

        elif url == "https://linkedin.com":
            b = PageBuilder()
            b.title_meta = "LinkedIn Page title"
            b.description_meta = "LinkedIn Page description"
            b.og_title = "LinkedIn Page og:title"
            b.og_description = "LinkedIn Page og:description"
            b.body_text = """LinkedIn body"""
            return b.build_contents()

        elif url == "https://page-with-last-modified-header.com":
            return webpage_html_favicon

        elif url == "https://robots-txt.com/robots.txt":
            return robots_txt_example_com_robots

        elif url.endswith("robots.txt"):
            return """  """

        elif url.endswith("sitemap.xml"):
            return """<urlset>
                      </urlset>"""

        b = PageBuilder()
        b.title_meta = "Page title"
        b.description_meta = "Page description"
        b.og_title = "Page og_title"
        b.og_description = "Page og_description"

        return b.build_contents()

    def get_contents_youtube_channel(self, url):
        if url == "https://youtube.com/channel/samtime/rss.xml":
            return webpage_samtime_youtube_rss

        elif url == "https://youtube.com/channel/2020-year-channel/rss.xml":
            return webpage_old_pubdate_rss

        elif url == "https://youtube.com/channel/no-pubdate-channel/rss.xml":
            return webpage_no_pubdate_rss

        elif url == "https://youtube.com/channel/airpano/rss.xml":
            return webpage_youtube_airpano_feed

        elif (
            url
            == "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        ):
            return webpage_samtime_youtube_rss

    def get_contents_instance(self, url):
        if (
            url
            == "https://instance.com/apps/rsshistory/entries-json/?query_type=recent"
        ):
            return instance_entries_json

        elif (
            url
            == "https://instance.com/apps/rsshistory/entries-json/?query_type=recent&source_title=Source100"
        ):
            return instance_entries_source_100_json

        elif (
            url
            == "https://instance.com/apps/rsshistory/entries-json/?query_type=recent&page=1"
        ):
            return """{}"""

        elif url == "https://instance.com/apps/rsshistory/source-json/100":
            return f'{{ "source": {instance_source_100_json} }}'

        elif url == "https://instance.com/apps/rsshistory/source-json/101":
            return f'{{ "source": {instance_source_101_json} }}'

        elif url == "https://instance.com/apps/rsshistory/source-json/102":
            return f'{{ "source": {instance_source_102_json} }}'

        elif url == "https://instance.com/apps/rsshistory/source-json/103":
            return f'{{ "source": {instance_source_103_json} }}'

        elif url == "https://instance.com/apps/rsshistory/source-json/104":
            return f'{{ "source": {instance_source_104_json} }}'

        elif url == "https://instance.com/apps/rsshistory/source-json/105":
            return f'{{ "source": {instance_source_105_json} }}'

        elif url == "https://instance.com/apps/rsshistory/entry-json/1912018":
            return """{}"""

        elif url == "https://instance.com/apps/rsshistory/sources-json":
            return instance_sources_page_1

        elif url == "https://instance.com/apps/rsshistory/sources-json/?page=1":
            return instance_sources_page_1

        elif url == "https://instance.com/apps/rsshistory/sources-json/?page=2":
            return instance_sources_page_2

        elif url == "https://instance.com/apps/rsshistory/sources-json/?page=3":
            return instance_sources_json_empty

        elif "/sources-json/":
            return instance_sources_json_empty

        elif "/entries-json/":
            return instance_entries_json_empty

        else:
            return """{}"""


class FakeInternetTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MockRequestCounter.mock_page_requests = 0

    def get_contents_function(self, url, headers, timeout_s, ping=False):
        print("Mocked Requesting page: {}".format(url))
        MockRequestCounter.mock_page_requests += 1

        return TestResponseObject(url, headers, timeout_s)

    def disable_web_pages(self):
        RequestBuilder.get_contents_function = self.get_contents_function

        # UrlHandler.youtube_video_handler = YouTubeVideoHandlerMock
        UrlHandler.youtube_video_handler = YouTubeJsonHandlerMock
        # channel uses RSS page to obtain data. We do not need to mock it
        # UrlHandler.youtube_channel_handler = YouTubeChannelHandlerMock
        # UrlHandler.odysee_video_handler = YouTubeVideoHandlerMock
        # UrlHandler.odysee_channel_handler = YouTubeVideoHandlerMock

    def setup_configuration(self):
        # each suite should start with a default configuration entry
        c = Configuration.get_object()
        c.config_entry = ConfigurationEntry.get()

        c.config_entry.enable_keyword_support = True
        c.config_entry.enable_domain_support = True
        c.config_entry.accept_domains = True
        c.config_entry.accept_not_domain_entries = True
        c.config_entry.new_entries_merge_data = False
        c.config_entry.new_entries_use_clean_data = False
        c.config_entry.new_source_enabled_state = False
        c.config_entry.auto_create_sources = False
        c.config_entry.auto_scan_entries = False
        c.config_entry.link_save = False
        c.config_entry.source_save = False
        c.config_entry.track_user_actions = False
        c.config_entry.days_to_move_to_archive = 100
        c.config_entry.days_to_remove_links = 0
        c.config_entry.respect_robots_txt = False
        c.config_entry.whats_new_days = 7
        c.config_entry.save()

        c.apply_robots_txt()

    def get_user(
        self, username="test_username", password="testpassword", is_superuser=False
    ):
        """
        TODO test cases should be rewritten to use names as follows:
         - test_superuser
         - test_staff
         - test_authenticated
        """
        users = User.objects.filter(username=username)
        if users.count() > 0:
            self.user = users[0]
            self.user.username = username
            self.user.password = password
            self.user.is_superuser = is_superuser
            self.user.save()
        else:
            self.user = User.objects.create_user(
                username=username, password=password, is_superuser=is_superuser
            )

        return self.user

    def print_errors(self):
        infos = AppLogging.objects.filter(level = int(logging.ERROR))
        for info in infos:
            print("Error: {}".format(info.info_text))

    def no_errors(self):
        infos = AppLogging.objects.filter(level = int(logging.ERROR))
        return infos.count() == 0

    def create_example_data(self):
        self.create_example_sources()
        self.create_example_links()
        self.create_example_domains()
        self.create_example_exports()

    def create_example_sources(self):
        source1 = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        source2 = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )
        return [source1, source2]

    def create_example_links(self):
        """
        All entries are outdated
        """
        entry1 = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        entry2 = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        entry3 = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        return [entry1, entry2, entry3]

    def create_example_domains(self):
        DomainsController.add("https://youtube.com?v=nonbookmarked")

        DomainsController.objects.create(
            protocol="https",
            domain="youtube.com",
            category="testCategory",
            subcategory="testSubcategory",
        )
        DomainCategories.objects.all().delete()
        DomainSubCategories.objects.all().delete()

    def create_example_keywords(self):
        datetime = KeyWords.get_keywords_date_limit() - timedelta(days=1)
        keyword = KeyWords.objects.create(keyword="test")
        keyword.date_published = datetime
        keyword.save()

        return [keyword]

    def create_example_exports(self):
        export1 = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        export2 = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        export3 = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        return [export1, export2, export3]

    def create_example_permanent_data(self):
        p1 = AppLogging.objects.create(info="info1", level=10, user="test")
        p1.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p1.save()

        p2 = AppLogging.objects.create(info="info2", level=10, user="test")
        p2.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p2.save()

        p3 = AppLogging.objects.create(info="info3", level=10, user="test")
        p3.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p3.save()

        return [p1, p2, p3]
