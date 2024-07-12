import waybackpy
import time
from datetime import datetime, date, timedelta

from waybackpy import WaybackMachineCDXServerAPI, WaybackMachineSaveAPI

from ..models import AppLogging
from ..apps import LinkDatabase
from ..webtools import DomainAwarePage


class WaybackMachine(object):
    def __init__(self, url=None):
        self.url = url

    def capture_limits(self, url):
        if self.url != url:
            self.url = url

            from ..webtools import RequestBuilder

            user_agent = RequestBuilder.user_agent

            cdx_api = WaybackMachineCDXServerAPI(url, user_agent)

            oldest = cdx_api.oldest()
            newest = cdx_api.newest()

            self.oldest = oldest.datetime_timestamp
            self.newest = newest.datetime_timestamp

    def get_formatted_date(self, time):
        return time.strftime("%Y%m%d")

    def get_archive_url(self, url, time):
        if self.url:
            if self.oldest.date() > time or self.newest.date() < time:
                return

        from ..webtools import RequestBuilder

        user_agent = RequestBuilder.user_agent

        cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
        handle = cdx_api.near(year=time.year, month=time.month, day=time.day, hour=12)

        archive_timestamp = str(handle.timestamp)
        time_text = self.get_formatted_date(time)

        if not archive_timestamp.startswith(time_text):
            LinkDatabase.info(archive_timestamp)
            LinkDatabase.info(time_text)
            return

        return_url = self.get_archive_url_with_overlay(
            handle.timestamp, handle.original
        )
        return return_url

    def get_archive_url_with_overlay(self, formatted_timestamp, url):
        return "https://web.archive.org/web/{}id_/{}".format(formatted_timestamp, url)

    def get_archive_url_for_timestamp(self, formatted_timestamp, url):
        return "https://web.archive.org/web/{}*/{}".format(formatted_timestamp, url)

    def get_archive_url_for_date(self, formatted_date, url):
        return "https://web.archive.org/web/{}000000*/{}".format(formatted_date, url)

    def get_archive_urls(self, url, start_time, stop_time):
        time = stop_time
        while time >= start_time:
            wayback_url = self.get_archive_url(url, time)
            yield (time, wayback_url)
            time -= timedelta(days=1)

    def save_impl(self, url):
        from ..webtools import RequestBuilder

        user_agent = RequestBuilder.user_agent

        save_api = WaybackMachineSaveAPI(url, user_agent)
        LinkDatabase.info("Save url {0}".format(url))
        try:
            val = save_api.save()
            return val
        except Exception as E:
            AppLogging.exc("WaybackMachine: save url: {0}".format(url))
            time.sleep(5)  # wait 5 seconds. Ain't nobody got time for that

    def save(self, url):
        ret = self.save_impl(url)
        if ret == None:
            return self.save_impl(url)
        else:
            return ret

    def is_saved(self, url):
        p = DomainAwarePage(url)
        if p.is_youtube():
            return False

        dom = p.get_domain_only()

        mainstream = ["www.facebook", "www.rumble", "wikipedia.org", "web.archive.org"]

        for item in mainstream:
            if dom.find(item) >= 0:
                return False

        return True

    def debug_handle(self, handle):
        LinkDatabase.info(handle)
        LinkDatabase.info(handle.archive_url)
        LinkDatabase.info(handle.original)
        LinkDatabase.info(handle.urlkey)
        LinkDatabase.info(handle.datetime_timestamp)
        LinkDatabase.info(handle.statuscode)
        LinkDatabase.info(handle.mimetype)
