import waybackpy
from waybackpy import WaybackMachineCDXServerAPI


class WaybackMachine(object):

    def __init__(self):
        pass

    def get_wayback_at_time(self, url, time):
        from ..webtools import Page

        user_agent = Page.user_agent

        cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
        handle = cdx_api.near(year=time.year, month=time.month, day=time.day)

        #if handle.timestamp == time.year + time.month

        #print(handle)
        #print(handle.archive_url)
        #print(handle.original)
        #print(handle.urlkey)
        #print(handle.timestamp)
        #print(handle.datetime_timestamp)
        #print(handle.statuscode)
        #print(handle.mimetype)

        return_url = "https://web.archive.org/web/" + handle.timestamp + "id_/"+handle.original
        return return_url
