import time
import ipaddress

from django.db import models
from django.db.models import Q, F

from webtoolkit import UrlLocation, is_status_code_invalid
from utils.dateutils import DateUtils

from ..models import (
    AppLogging,
    KeyWords,
    EntryRules,
    SocialData,
)
from ..configuration import Configuration
from ..apps import LinkDatabase
from .entries import LinkDataController
from .entrywrapper import EntryWrapper
from .entriesutils import add_all_domains, EntryContentsCrawler
from .backgroundjob import BackgroundJobController
from .domains import DomainsController
from .sources import SourceDataController


class EntryDataBuilder(object):
    """
    - sometimes we want to call this object directly, sometimes it should be redirected to "add link background job"
    - we do not change data in here, we do not correct, we just follow it (I think that is what should be)
    - all subservent entries are added by background controller, handled in a separate task
    - we cannot spend too much time in builder from any context. This code should be possibly fast
    - if there is a possibility to not search it, we do not do it
    """

    def __init__(
        self,
        link=None,
        link_data=None,
        source_is_auto=True,
        user=None,
        allow_recursion=True,
        ignore_errors=False,
        strict_ids=False,
        browser=None,
    ):
        self.link = link
        self.link_data = link_data
        self.source_is_auto = source_is_auto
        self.allow_recursion = allow_recursion
        self.user = user
        self.strict_ids = strict_ids
        self.browser = browser
        self.errors = []

        self.ignore_errors = ignore_errors
        c = Configuration.get_object().config_entry
        if c.accept_dead_links:
            self.ignore_errors = True

        self.result = None

        if self.link:
            self.build_from_link()

        if self.link_data:
            self.build_from_props(ignore_errors=self.ignore_errors)

    def build(
        self,
        link=None,
        link_data=None,
        source_is_auto=True,
        allow_recursion=True,
        ignore_errors=False,
        strict_ids=False,
        browser=None,
    ):
        self.link = link
        self.link_data = link_data
        self.strict_ids = strict_ids
        self.source_is_auto = source_is_auto
        self.browser = browser

        if self.link:
            return self.build_from_link()

        if self.link_data:
            return self.build_from_props(ignore_errors=self.ignore_errors)

    def build_simple(self, link=None, user=None, source_is_auto=True, browser=None):
        if link:
            self.link = link

        self.user = user
        self.source_is_auto = source_is_auto
        self.browser = browser

        if not self.is_enabled_to_store_link():
            return

        wrapper = EntryWrapper(link=self.link)
        entry = wrapper.get()
        if entry:
            self.result = entry
            return entry

        link_data = {}
        link_data["link"] = self.link
        link_data["user"] = self.user

        entry = wrapper.create(link_data)

        if entry:
            BackgroundJobController.entry_update_data(entry=entry, browser=self.browser)
            BackgroundJobController.link_scan(entry=entry, browser=browser)
            BackgroundJobController.link_save(entry.link)

        return entry

    def build_from_link(self, link=None, ignore_errors=False):
        if link:
            self.link = link

        """
        TODO extract this to a separate class?
        """
        self.ignore_errors = ignore_errors
        self.link = UrlLocation.get_cleaned_link(self.link)
        if not self.link:
            return

        p = UrlLocation(self.link)
        if p.is_link_service():
            return self.build_from_link_service()
        else:
            return self.build_from_normal_link()

    def build_from_link_service(self):
        from ..pluginurl import EntryUrlInterface

        if not self.is_enabled_to_store_link():
            return

        url = EntryUrlInterface(self.link, ignore_errors=self.ignore_errors)
        self.link_data = url.get_props()

        if url.is_server_error():
            raise IOError(f"{self.link}: Crawling server error")

        if self.source_is_auto and not url.is_valid():
            self.errors.append("Url:{}. Url is not valid. Check status code, etc.".format(self.link))
            return

        if not self.is_enabled_to_store(url.handler):
            return

        return self.build_from_props(ignore_errors=self.ignore_errors)

    def build_from_normal_link(self):
        from ..pluginurl import EntryUrlInterface

        """
        TODO move this to a other class OnlyLinkDataBuilder?
        """
        if not self.is_enabled_to_store_link():
            return

        wrapper = EntryWrapper(link=self.link)
        obj = wrapper.get()
        if obj:
            self.result = obj
            return obj

        if not self.link_data:
            self.link_data = {}

        self.link_data["link"] = self.link

        config_entry = Configuration.get_object().config_entry

        url = EntryUrlInterface(
            self.link, ignore_errors=self.ignore_errors, browser=self.browser
        )

        self.link_data = url.get_props()
        if not self.link_data:
            self.errors.append("Url:{}. Could not obtain link data".format(self.link))
            return

        # we do not want to obtain properties for non-domain entries, if we capture only
        # domains
        if not self.is_enabled_to_store(url.handler):
            return

        if url.is_server_error():
            raise IOError(f"{self.link}: Crawling server error")

        self.merge_link_data(self.link_data)

        if self.link_data:
            return self.build_from_props_internal()
        else:
            if config_entry.debug_mode:
                self.errors.append(
                    "Url:{}. Could not obtain properties for link.".format(self.link)
                )
                AppLogging.debug(
                    'Url:{} Could not obtain properties for link.'.format(self.link)
                )

    def merge_link_data(self, link_data):
        # TODO update missing keys - do not replace them
        new_link_data = None

        if self.link_data and link_data:
            new_link_data = {**self.link_data, **link_data}
        if self.link_data:
            new_link_data = self.link_data
        if link_data:
            new_link_data = link_data

        self.link_data = new_link_data
        return self.link_data

    def is_property_set(self, link_data, property_name):
        return (
            property_name in link_data
            and link_data[property_name] != None
            and len(link_data[property_name]) > 0
        )

    def is_link_data_valid_for_auto_add(self, link_data):
        if not self.is_property_set(link_data, "title"):
            return False

        if "status_code" in link_data and link_data["status_code"]:
            if is_status_code_invalid(link_data["status_code"]):
                return False

        if "is_valid" in link_data and not link_data["is_valid"]:
            return False

        return True

    def build_from_props(self, ignore_errors=False):
        self.ignore_errors = ignore_errors

        if "link" not in self.link_data:
            return

        self.link = self.link_data["link"]
        if not self.link:
            return

        obj = None

        self.link_data["link"] = UrlLocation.get_cleaned_link(self.link_data["link"])
        self.link = self.link_data["link"]

        if not self.is_enabled_to_store_link():
            return

        self.add_domain()

        if self.is_too_old():
            return

        wrapper = EntryWrapper(link=self.link)
        entry = wrapper.get()
        if entry:
            self.result = entry
            return entry

        if not self.is_enabled_to_store():
            return

        entry = self.build_from_props_internal()
        self.result = entry
        return entry

    def is_too_old(self):
        day_to_remove = Configuration.get_object().get_entry_remove_date()
        if not day_to_remove:
            return False

        if (
            self.source_is_auto
            and "date_published" in self.link_data
            and self.link_data["date_published"]
        ):
            if self.link_data["date_published"] < day_to_remove:
                return True

        return False

    def build_from_props_internal(self):
        from .entryupdater import EntryUpdater
        entry = None

        # we obtain links from various places. We do not want technical links with no data, redirect, CDN or other
        self.link_data = self.get_clean_link_data()

        # if self.source_is_auto:
        #    self.link_data["link"] = self.link_data["link"].lower()

        c = Configuration.get_object().config_entry

        date = None
        if "date_published" in self.link_data:
            date = self.link_data["date_published"]
        wrapper = EntryWrapper(link=self.link_data["link"], date=date)
        entry = wrapper.get()

        if entry:
            return entry

        self.link_data = self.check_and_set_source_object()
        self.link_data = self.set_domain_object()

        entry = self.add_entry_internal()

        # TODO if object just created
        if entry:
            c = Configuration.get_object().config_entry
            if c.new_entries_use_clean_data:
                BackgroundJobController.entry_reset_data(entry)
            elif c.new_entries_merge_data:
                BackgroundJobController.entry_update_data(entry)

            updater = EntryUpdater(entry=entry)
            updater.reset_local_data()

            self.add_addition_link_data(entry)

        return entry

    def get_clean_link_data(self):
        props = self.link_data
        props = LinkDataController.get_clean_data(props)
        return props

    def is_domain_link_data(self):
        link_data = self.link_data
        p = UrlLocation(link_data["link"])
        return p.get_domain().url == link_data["link"]

    def add_entry_internal(self):
        link_data = self.link_data

        new_link_data = dict(link_data)
        if "date_published" not in new_link_data:
            new_link_data["date_published"] = DateUtils.get_datetime_now_utc()
        if "date_update_last" not in new_link_data:
            new_link_data["date_update_last"] = DateUtils.get_datetime_now_utc()

        if (
            "page_rating" not in new_link_data
            or "page_rating" in new_link_data
            and new_link_data["page_rating"] == 0
        ):
            if "page_rating_contents" in new_link_data:
                new_link_data["page_rating"] = new_link_data["page_rating_contents"]

        if "age" not in new_link_data:
            age = EntryRules.get_age_for_dictionary(new_link_data)
            if age:
                new_link_data["age"] = age

        AppLogging.debug("Adding link: {}".format(new_link_data["link"]))

        wrapper = EntryWrapper(
            link=new_link_data["link"],
            date=new_link_data["date_published"],
            user=self.user,
            strict_ids=self.strict_ids,
        )

        entry = wrapper.create(new_link_data)

        if entry:
            BackgroundJobController.link_scan(entry=entry)

        return entry

    def set_domain_object(self):
        config = Configuration.get_object().config_entry

        if config.enable_domain_support:
            domain = DomainsController.add(self.link_data["link"])

            if domain:
                self.link_data["domain"] = domain
        return self.link_data

    def check_and_set_source_object(self):
        link_data = self.link_data

        if "source" not in link_data and "source_url" in link_data:
            source_obj = None
            sources = SourceDataController.objects.filter(url=link_data["source_url"])
            if sources.exists():
                source_obj = sources[0]

            link_data["source"] = source_obj

        return link_data

    def is_enabled_to_store_link(self):
        if not self.source_is_auto:
            return True

        link = self.link

        if not link:
            self.errors.append(
                "Url:{}. Link was rejected - missing link.".format(self.link)
            )
            return False

        if len(link) > LinkDataController.get_field_length("link"):
            self.errors.append("Url:{}. Link too long".format(link))
            return False

        location = UrlLocation(link)
        domain = location.get_domain_only()

        config = Configuration.get_object().config_entry
        if not config.accept_ip_links:
            if self.is_ipv4(domain):
                return False

        if location.is_onion() and not config.accept_onion_links:
            return False

        is_domain = location.is_domain()
        if is_domain and not config.accept_domain_links:
            return False
        elif not is_domain and not config.accept_non_domain_links:
            return False

        rule = EntryRules.is_url_blocked(link)
        if rule:
            self.errors.append(
                "Url:{}. Link was rejected because of a rule. {}".format(
                    link, rule
                )
            )
            return False

        return True

    def is_enabled_to_store(self, url_handler=None):
        # manual entry is always enabled
        if not self.source_is_auto:
            return True

        config = Configuration.get_object().config_entry
        link = self.link_data["link"]

        location = UrlLocation(link)
        is_domain = location.is_domain()
        domain = location.get_domain_only()

        if "title" not in self.link_data or not self.link_data["title"]:
            self.errors.append(
                "Url:{}. Link was rejected - missing title.".format(self.link)
            )
            return False

        if url_handler and not url_handler.is_valid():
            self.errors.append("Url:{}. Url is not valid".format(self.link))
            return False

        # we do not store link services, we can store only what is behind those links
        if location.is_link_service():
            self.errors.append("Url:{}. Url is link service".format(self.link))
            return False

        # heavier checks last
        if self.is_live_video():
            self.errors.append("Url:{}. Url is live video".format(self.link))
            return False

        if EntryRules.is_dict_blocked(self.link_data):
            self.errors.append(
                "Url:{}. Link was rejected due contents rule - by checking properties.".format(
                    self.link
                )
            )
            return False

        if not self.is_link_data_valid_for_auto_add(self.link_data):
            self.errors.append(
                "Url:{}. Link is not valid for auto add".format(self.link)
            )
            return False

        if not config.accept_same_hashes:
            if url_handler:
                response = url_handler.get_response()

                hash = response.get_hash()
                body_hash = response.get_body_hash()

                if hash and LinkDataController.objects.filter(contents_hash = hash).count() > 0:
                    self.errors.append(
                        "Url:{}. Not accepting same hashes".format(self.link)
                    )
                    return False
                if body_hash and LinkDataController.objects.filter(body_hash = body_hash).count() > 0:
                    self.errors.append(
                        "Url:{}. Not accepting same hashes - body".format(self.link)
                    )
                    return False

        return True

    def is_ipv4(self, string):
        try:
            ipaddress.IPv4Network(string)
            return True
        except ValueError:
            return False

    def is_live_video(self):
        link_data = self.link_data

        if "live" in link_data and link_data["live"]:
            return link_data["live"]

        return False

    def add_addition_link_data(self, entry):
        link_data = self.link_data
        config = Configuration.get_object().config_entry

        self.add_sub_links(entry)
        # self.add_keywords(entry) # TODO
        self.add_socialdata(entry)

        if config.auto_scan_new_entries:
            BackgroundJobController.link_scan(link_data["link"])

        if entry:
            self.download_thumbnail(entry.thumbnail)

    def add_socialdata(self, entry):
        config = Configuration.get_object().config_entry
        if config.new_entries_fetch_social_data:
            SocialData.get(entry)

    def download_thumbnail(self, thumbnail_path):
        if thumbnail_path:
            config = Configuration.get_object().config_entry
            if config.auto_store_thumbnails:
                BackgroundJobController.download_file(thumbnail_path)

    def add_sub_links(self, entry):
        """
        Adds links from description of that link.
        Store link as-is.
        """
        config = Configuration.get_object().config_entry

        link_data = self.link_data
        source = link_data.get("source")

        links = self.get_sub_links(entry)

        for link in links:
            BackgroundJobController.link_add(url=link, source=source)

    def get_sub_links(self, entry):
        config = Configuration.get_object().config_entry

        link_data = self.link_data
        link = link_data.get("link")
        links = set()

        if config.enable_crawling and config.auto_scan_new_entries:
            source = link_data.get("source")

            description = link_data.get("description")
            crawler = EntryContentsCrawler(link_data["link"], description, source)
            links.update(crawler.get_links())

            contents = link_data.get("contents")
            crawler = EntryContentsCrawler(link_data["link"], contents, source)
            links.update(crawler.get_links())

        links -= {link}

        return links

    def add_domain(self):
        config = Configuration.get_object().config_entry
        link_data = self.link_data
        link = link_data.get("link")

        if config.enable_crawling and config.auto_crawl_sources:
            if config.accept_domain_links:
                add_all_domains(link)

    def add_keywords(self, entry):
        config = Configuration.get_object().config_entry

        if config.enable_keyword_support:
            if entry.title and entry.title != "":
                KeyWords.add_link_data(entry.title)

    def read_domains_from_bookmarks():
        objs = LinkDataController.objects.filter(bookmarked=True)
        for obj in objs:
            p = UrlLocation(obj.link)
            EntryDataBuilder(link=p.get_domain().url)
