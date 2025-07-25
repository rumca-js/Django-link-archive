"""
This module provides replacement for the Internet.

 - when test make requests to obtain a page, we return artificial data here
 - when there is a request to obtain youtube JSON data, we provide artificial data, etc.
"""

import logging
import json
import psutil
import os
from django.test import TestCase
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from ..webtools import (
    YouTubeVideoHandler,
    YouTubeJsonHandler,
    YouTubeChannelHandler,
    OdyseeVideoHandler,
    OdyseeChannelHandler,
    HttpPageHandler,
    Url,
    HttpRequestBuilder,
    PageResponseObject,
    WebLogger,
    WebConfig,
    CrawlerInterface,
    RemoteServer,
)

from ..models import (
    AppLogging,
    ConfigurationEntry,
    Browser,
    EntryRules,
    SearchView,
)
from ..configuration import Configuration
from ..pluginurl import UrlHandlerEx

from .fake.remoteserver import (
    remote_server_json,
)
from .fake.geekwirecom import (
    geekwire_feed,
)
from .fake.firebog import (
    firebog_adguard_list,
    firebog_w3kbl_list,
    firebog_tick_lists,
    firebog_malware,
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


class DjangoRequestObject(object):
    """
    Used to mock django request object
    """

    def __init__(self, user):
        self.user = user


class MockRequestCounter(object):
    mock_page_requests = 0
    request_history = []

    def requested(url, info=None, settings=None):
        """
        Info can be a dict
        """
        if info:
            MockRequestCounter.request_history.append({"url": url, "info": info})
        elif settings:
            MockRequestCounter.request_history.append(
                {"url": url, "settings": settings}
            )
        else:
            MockRequestCounter.request_history.append({"url": url})
        MockRequestCounter.mock_page_requests += 1

    def reset():
        MockRequestCounter.mock_page_requests = 0
        MockRequestCounter.request_history = []


class DefaultCrawler(CrawlerInterface):

    def run(self):
        MockRequestCounter.requested(self.request.url)


class FakeInternetData(object):
    def __init__(self, url):
        self.url = url
        self.properties = {
            "link": self.url,
            "title": "Title",
            "description": "Description",
            "date_published": DateUtils.get_datetime_now_iso(),
            "author": "Description",
            "language": "Language",
            "album": "Description",
            "page_rating": 80,
            "thumbnail": None,
        }

        self.response = {
            "status_code": 200,
            "Content-Length": 200,
            "Content-Type": "text/html",
            "body_hash": b"01001012",
            "hash": b"01001012",
            "is_valid": True,
        }
        self.text_data = "Something"
        self.binary_data = None
        self.entries = []

    def get_all_properties(self):
        data = []
        data.append({"name": "Properties", "data": self.properties})
        data.append({"name": "Text", "data": {"Contents": self.text_data}})
        data.append({"name": "Binary", "data": {"Contents": self.binary_data}})
        data.append({"name": "Settings", "data": None})
        data.append({"name": "Response", "data": self.response})
        data.append({"name": "Headers", "data": {}})
        data.append({"name": "Entries", "data": self.entries})

        return data

    def get_getj(self, name="", settings=None):
        if self.url == "https://linkedin.com":
            self.properties["title"] = "Https LinkedIn Page title"
            self.properties["description"] = "Https LinkedIn Page description"
        elif self.url == "https://m.youtube.com/watch?v=1234":
            self.properties["link"] = "https://www.youtube.com/watch?v=1234"
            self.properties["feeds"] = [
                "https://www.youtube.com/feeds/videos.xml?channel_id=1234-channel-id",
            ]
            self.properties["title"] = "YouTube 1234 video"
            self.properties["language"] = None
        elif self.url == "https://www.youtube.com/watch?v=1234":
            self.properties["link"] = "https://www.youtube.com/watch?v=1234"
            self.properties["feeds"] = [
                "https://www.youtube.com/feeds/videos.xml?channel_id=1234-channel-id",
            ]
            self.properties["title"] = "YouTube 1234 video"
            self.properties["language"] = None
        elif self.url == "https://youtu.be/1234":
            self.properties["link"] = "https://www.youtube.com/watch?v=1234"
            self.properties["feeds"] = [
                "https://www.youtube.com/feeds/videos.xml?channel_id=1234-channel-id",
            ]
            self.properties["title"] = "YouTube 1234 video"
            self.properties["language"] = None
        elif self.url == "https://www.reddit.com/r/searchengines/":
            self.properties["feeds"] = ["https://www.reddit.com/r/searchengines/.rss"]
        elif self.url == "https://www.reddit.com/r/searchengines":
            self.properties["feeds"] = ["https://www.reddit.com/r/searchengines/.rss"]
        elif self.url == "https://www.reddit.com/r/searchengines/.rss":
            self.set_entries(10)
        elif self.url == "https://page-with-rss-link.com":
            self.properties["title"] = "Page with RSS link"
            self.properties["feeds"] = ["https://page-with-rss-link.com/feed"]
        elif self.url == "https://page-with-rss-link.com/feed":
            self.set_entries(10)
            self.response["Content-Type"] = "application/rss+xml"
            self.properties["title"] = "Page with RSS link - RSS contents"
        elif self.url == "https://www.codeproject.com/WebServices/NewsRSS.aspx":
            self.set_entries(13)
            self.response["Content-Type"] = "application/rss+xml"
            self.properties["thumbnail"] = (
                "https://www.codeproject.com/App_Themes/Std/Img/logo100x30.gif"
            )
        elif self.url == "https://no-props-page.com":
            self.properties["title"] = None
            self.properties["description"] = None
            self.properties["date_published"] = None
            self.properties["author"] = None
            self.properties["language"] = None
            self.properties["album"] = None
            self.properties["page_rating"] = 0
            self.properties["thumbnail"] = None
        elif self.url == "https://page-with-http-status-500.com":
            self.response["status_code"] = 500
            self.response["is_valid"] = False
        elif self.url == "https://page-with-http-status-400.com":
            self.response["status_code"] = 400
            self.response["is_valid"] = False
        elif self.url == "https://page-with-http-status-300.com":
            self.response["status_code"] = 300
            self.response["is_valid"] = True
        elif self.url == "https://page-with-http-status-200.com":
            self.response["status_code"] = 200
            self.response["is_valid"] = True
        elif self.url == "https://page-with-http-status-100.com":
            self.response["status_code"] = 100
            self.response["is_valid"] = False
        elif self.url == "http://page-with-http-status-500.com":
            self.response["status_code"] = 500
            self.response["is_valid"] = False
        elif self.url == "http://page-with-http-status-400.com":
            self.response["status_code"] = 400
            self.response["is_valid"] = False
        elif self.url == "http://page-with-http-status-300.com":
            self.response["status_code"] = 300
        elif self.url == "http://page-with-http-status-200.com":
            self.response["status_code"] = 200
        elif self.url == "http://page-with-http-status-100.com":
            self.response["status_code"] = 100
            self.response["is_valid"] = False
        elif self.url == "https://www.youtube.com/watch?v=666":
            self.response["status_code"] = 500
            self.response["is_valid"] = False
        elif self.url == "https://invalid.rsspage.com/rss.xml":
            self.response["status_code"] = 500
        elif (
            self.url
            == "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        ):
            self.set_entries(13)
            self.response["Content-Type"] = "application/rss+xml"
            self.properties["feeds"] = [self.url]
        elif (
            self.url
            == "https://www.youtube.com/feeds/videos.xml?channel_id=NOLANGUAGETIMESAMTIMESAM"
        ):
            self.set_entries(13, language=None)
            self.response["Content-Type"] = "application/rss+xml"
            self.properties["feeds"] = [self.url]
            self.properties["language"] = None
        elif self.url.startswith("https://odysee.com/$/rss"):
            self.set_entries(13)
            self.response["Content-Type"] = "application/rss+xml"
            self.properties["feeds"] = [self.url]
        elif self.url == "https://www.geekwire.com/feed":
            self.text_data = geekwire_feed
            self.response["Content-Type"] = "application/rss+xml"
            self.properties["feeds"] = [self.url]
        elif (
            self.url
            == "https://www.youtube.com/feeds/videos.xml?channel_id=1234-channel-id"
        ):
            self.set_entries(13)
            self.response["Content-Type"] = "application/rss+xml"
            self.properties["feeds"] = [self.url]
        elif self.url == "https://instance.com/apps/rsshistory/sources-json":
            self.properties["title"] = "Instance Proxy"
        elif self.url == "https://v.firebog.net/hosts/AdguardDNS.txt":
            self.text_data = firebog_adguard_list
        elif self.url == "https://v.firebog.net/hosts/static/w3kbl.txt":
            self.text_data = firebog_w3kbl_list
        elif self.url == "https://v.firebog.net/hosts/lists.php?type=tick":
            self.text_data = firebog_tick_lists
        elif self.url == "https://v.firebog.net/hosts/RPiList-Malware.txt":
            self.text_data = firebog_malware
        elif self.url == "https://casino.com":
            self.properties["title"] = "Casino Casino Casino"
            self.properties["description"] = "Casino Casino Casino"
        elif self.url == "https://nfsw.com":
            self.properties["title"] = "AI NSFW girlfriend"
            self.properties["description"] = "AI NSFW girlfriend"
        elif self.url == "https://binary.com/file":
            self.properties["title"] = ""
            self.properties["description"] = ""
            self.binary_data = "text".encode()

        if self.url.find("reddit") >= 0:
            self.properties["language"] = "en"

        return self.get_all_properties()

    def set_entries(self, number=1, language="en"):
        for item in range(0, number):
            properties = {}
            properties["link"] = self.url + str(item)
            properties["title"] = "Title" + str(item)
            properties["description"] = "Description" + str(item)
            properties["date_published"] = DateUtils.get_datetime_now_iso()
            properties["author"] = "Description"
            properties["language"] = language
            properties["album"] = "Description"
            properties["page_rating"] = 80
            properties["thumbnail"] = None

            self.entries.append(properties)


class FakeInternetTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MockRequestCounter.reset()

        self._process = psutil.Process(os.getpid())
        self._mem_before = self._get_memory_mb()

    def _get_memory_mb(self):
        return self._process.memory_info().rss / 1024 / 1024

    def check_memory(self):
        mem_after = self._get_memory_mb()
        print(f"[TEARDOWN] Memory after test: {mem_after:.2f} MB")
        mem_delta = mem_after - self._mem_before
        print(f"[TEARDOWN] Memory change: {mem_delta:.2f} MB")

        # Fail the test if memory usage increased too much
        threshold_mb = 10
        self.assertLess(
            mem_delta,
            threshold_mb,
            f"Memory increased by {mem_delta:.2f} MB — possible leak?",
        )

    def disable_web_pages(self):
        WebLogger.web_logger = AppLogging
        WebConfig.get_default_crawler = FakeInternetTestCase.get_default_crawler
        WebConfig.get_crawler_from_mapping = (
            FakeInternetTestCase.get_crawler_from_mapping
        )
        RemoteServer.get_getj = self.get_getj
        RemoteServer.get_socialj = self.get_socialj
        UrlHandlerEx.ping = FakeInternetTestCase.ping

        c = Configuration.get_object()
        c.config_entry = ConfigurationEntry.get()

        if c.config_entry.remote_webtools_server_location == "":
            c.config_entry.remote_webtools_server_location = "https://127.0.0.1:3000"
            c.config_entry.save()

    def ping(url):
        if url == "https://page-with-http-status-500.com":
            return False
        elif url == "https://page-with-http-status-400.com":
            return False
        elif url == "https://page-with-http-status-100.com":
            return False
        elif url == "http://page-with-http-status-500.com":
            return False
        elif url == "http://page-with-http-status-400.com":
            return False
        elif url == "http://page-with-http-status-100.com":
            return False

        return True

    def get_getj(self, url, name="", settings=None):
        # print("FakeInternet:get_getj: Url:{}".format(url))
        # return json.loads(remote_server_json)
        MockRequestCounter.requested(url=url, info=settings)

        data = FakeInternetData(url)
        return data.get_getj(name, settings)

    def get_socialj(self, url):
        MockRequestCounter.requested(url=url)
        return None

    def get_default_crawler(url):
        crawler = DefaultCrawler(url=url)

        crawler_data = {
            "name": "DefaultCrawler",
            "crawler": crawler,
            "settings": {
                "timeout_s": 10,
            },
        }

        return crawler_data

    def get_crawler_from_mapping(request, crawler_data):
        if "settings" in crawler_data:
            crawler = DefaultCrawler(request=request, settings=crawler_data["settings"])
        else:
            crawler = DefaultCrawler(request=request)
        crawler.crawler_data = crawler_data

        return crawler

    def setup_configuration(self):
        # each suite should start with a default configuration entry
        c = Configuration.get_object()
        c.config_entry = ConfigurationEntry.get()

        c.config_entry.enable_keyword_support = True
        c.config_entry.enable_domain_support = True
        c.config_entry.accept_domain_links = True
        c.config_entry.accept_non_domain_links = True
        c.config_entry.new_entries_merge_data = False
        c.config_entry.new_entries_use_clean_data = False
        c.config_entry.default_source_state = False
        c.config_entry.auto_create_sources = False
        c.config_entry.auto_scan_new_entries = False
        c.config_entry.enable_link_archiving = False
        c.config_entry.enable_source_archiving = False
        c.config_entry.track_user_actions = False
        c.config_entry.track_user_searches = False
        c.config_entry.track_user_navigation = False
        c.config_entry.days_to_move_to_archive = 100
        c.config_entry.days_to_remove_links = 0
        c.config_entry.whats_new_days = 7
        c.config_entry.entry_update_via_internet = True
        c.remote_webtools_server_location = "https://127.0.0.1:3000"

        c.config_entry.save()

        SearchView.objects.create(
            name="Default", order_by="-date_created, link", default=True
        )

        EntryRules.objects.create(
            rule_name="casinos-block",
            trigger_text="casino, lotter, jackpot, bingo, poker, slot, betting, togel, gacor, bandar judi, pagcor, slotlara kadar, canli bahis, terpopuler, deposit, g2gbet, terpercaya, maxtoto, Gampang, bonus giveaway, pg slot, cashback rewards, situs slot, slot situs",
            block=True,
        )

        EntryRules.objects.create(
            rule_name="sexual-block",
            trigger_text="mastubat, porn, sexseite, zoophilia, chaturbat",
            block=True,
        )

        EntryRules.objects.create(
            rule_name="inactive-links",
            trigger_text="forbidden, access denied, page not found, site not found, 404 not found, 404: not found, error 404, 404 error, 404 page, 404 file not found, squarespace - website expired, domain name for sale, account suspended, the request could not be satisfied",
            trigger_text_fields="title",
            block=True,
        )

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
        infos = AppLogging.objects.filter(level=int(logging.ERROR))
        for info in infos:
            print("Error: {}".format(info.info_text))

    def no_errors(self):
        infos = AppLogging.objects.filter(level=int(logging.ERROR))
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
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        entry2 = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        entry3 = LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source=source_youtube,
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
