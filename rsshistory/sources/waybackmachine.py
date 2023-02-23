import waybackpy
import time
from datetime import datetime, date, timedelta

from waybackpy import WaybackMachineCDXServerAPI, WaybackMachineSaveAPI

from ..models import PersistentInfo


class WaybackMachine(object):

    def __init__(self):
        self.url = None

    def capture_limits(self, url):
        if self.url != url:
            self.url = url

            from ..webtools import Page
            user_agent = Page.user_agent

            cdx_api = WaybackMachineCDXServerAPI(url, user_agent)

            oldest = cdx_api.oldest()
            newest = cdx_api.newest()

            self.oldest = oldest.datetime_timestamp
            self.newest = newest.datetime_timestamp

    def get_formatted_date(self, time):
        return time.strftime("%Y%m%d")

    def get_archive_url(self, url, time):
        # self.capture_limits(url)

        if self.url:
            if self.oldest.date() > time or self.newest.date() < time:
                return

        from ..webtools import Page
        user_agent = Page.user_agent
        #print("Time: {0} {1} {2} {3}".format(time.year, time.month, time.day, url))

        cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
        handle = cdx_api.near(year=time.year, month=time.month, day=time.day, hour=12)

        #print(handle)
        #print(handle.archive_url)
        #print(handle.original)
        #print(handle.urlkey)
        #print(handle.datetime_timestamp)
        #print(handle.statuscode)
        #print(handle.mimetype)

        archive_timestamp = str(handle.timestamp)
        time_text = self.get_formatted_date(time)

        if not archive_timestamp.startswith(time_text):
            print(archive_timestamp)
            print(time_text)
            return

        return_url = "https://web.archive.org/web/" + handle.timestamp + "id_/"+handle.original
        return return_url

    def get_archive_urls(self, url, start_time, stop_time):
        from ..models import RssSourceImportHistory

        time = stop_time
        while time >= start_time:
            #print("Time: {0}".format(time))
            if len(RssSourceImportHistory.objects.filter(url = url, date = time)) != 0:
                time -= timedelta(days = 1)
                continue

            wayback_url = self.get_archive_url(url, time)
            yield (time, wayback_url)
            time -= timedelta(days = 1)

    def save_impl(self, url):
        from ..webtools import Page

        user_agent = Page.user_agent

        save_api = WaybackMachineSaveAPI(url, user_agent)
        print("Saved url {0}".format(url))
        try:
            val = save_api.save()
            return val
        except Exception as e:
            print("WaybackMachine: save url: {0} {1}".format(url, str(e)))
            PersistentInfo.error("WaybackMachine: save url: {0} {1}".format(url, str(e)))
            time.sleep(5 * 3600) # wait 5 minute

    def save(self, url):
        ret = self.save_impl(url)
        if ret == None:
            return self.save_impl(url)
        else:
            return ret

