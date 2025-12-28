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

from webtoolkit import (
    RemoteServer,
    PageRequestObject,
    PageResponseObject,
    CrawlerInterface,
    HTTP_STATUS_USER_AGENT,
    HTTP_STATUS_TOO_MANY_REQUESTS,
    HTTP_STATUS_CODE_EXCEPTION,
    HTTP_STATUS_CODE_SERVER_ERROR,
    HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS,
    json_encode_field,
    json_decode_field,

    WebLogger,
)
from webtoolkit.tests.fake.geekwirecom import (
    geekwire_feed,
)
from webtoolkit.tests.fake.firebog import (
    firebog_adguard_list,
    firebog_w3kbl_list,
    firebog_tick_lists,
    firebog_malware,
)

from webtoolkit.tests.fake.instance import (
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

from webtoolkit.tests.fakeresponse import FakeInternetData
from webtoolkit.tests.mocks import MockRequestCounter

from ..models import (
    AppLogging,
    ConfigurationEntry,
    Browser,
    EntryRules,
    SearchView,
)
from ..controllers import SystemOperationController
from ..configuration import Configuration
from ..pluginurl import UrlHandler


class DjangoRequestObject(object):
    """
    Used to mock django request object
    """

    def __init__(self, user):
        self.user = user


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

        RemoteServer.get_getj = self.get_getj
        RemoteServer.get_socialj = self.get_socialj
        RemoteServer.get_feedsj = self.get_feedsj
        RemoteServer.get_pingj = self.get_pingj
        RemoteServer.get_infoj = self.get_infoj

        UrlHandler.ping = FakeInternetTestCase.ping
        # TODO this is not needed any more

        SystemOperationController.is_crawling_response_ok = self.is_crawling_response_ok

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

    def get_getj(self, request=None, url=None):
        #AppLogging.error("stack", stack=True)
        if url:
            print("FakeInternet:get_getj: Url:{}".format(url))
        elif request.url:
            print("FakeInternet:get_getj: Url:{}".format(request.url))

        if url and not request:
            request = PageRequestObject(url)
            request.url = url
            request.url = request.url.strip()

        MockRequestCounter.requested(url=request.url, info=request)

        data = FakeInternetData(request.url)
        return data.get_getj(request=request, url=url)

    def get_socialj(self, request=None, url=None):
        if url:
            print("FakeInternet:get_socialj: Url:{}".format(url))
        elif request.url:
            print("FakeInternet:get_socialj: Url:{}".format(request.url))
        MockRequestCounter.requested(url=url)

        data = FakeInternetData(url)
        return data.get_socialj(url)

    def get_feedsj(self, request=None, url=None):
        if url:
            print("FakeInternet:get_feedsj: Url:{}".format(url))
        elif request.url:
            print("FakeInternet:get_feedsj: Url:{}".format(request.url))
        data = FakeInternetData(url)
        return data.get_feedsj(url, settings=settings)

    def get_pingj(self, request=None, url=None):
        if url:
            print("FakeInternet:get_pingj: Url:{}".format(url))
        elif request.url:
            print("FakeInternet:get_pingj: Url:{}".format(request.url))
        data = FakeInternetData(url)
        return data.ping(url, settings=settings)

    def get_infoj(self):
        data = {"crawlers": [
                {
                   "enabled": True,
                   "name": "MockCrawler",
                   "settings": {
                       "timeout_s": 20
                   }
                },
                {
                   "enabled": True,
                   "name": "MockCrawler2",
                   "settings": {
                       "timeout_s": 27
                   }
                }
                ]
               }
        return data

    def is_crawling_response_ok(self, crawling_server):
        return True

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
