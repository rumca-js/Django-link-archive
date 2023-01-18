import waybackpy
from waybackpy import WaybackMachineCDXServerAPI, WaybackMachineSaveAPI
from ..models import PersistentInfo


class WaybackMachine(object):

    def __init__(self):
        pass

    def get_wayback_at_time(self, url, time):
        from ..webtools import Page

        user_agent = Page.user_agent

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
        time_text = time.strftime("%Y%m%d")


        if not archive_timestamp.startswith(time_text):
            print(archive_timestamp)
            print(time_text)
            return

        return_url = "https://web.archive.org/web/" + handle.timestamp + "id_/"+handle.original
        return return_url

    def save(self, url):
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
