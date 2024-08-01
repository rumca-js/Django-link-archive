"""
This is example script about how to use this project as a simple RSS reader
"""
import socket
import json
import traceback

from rsshistory.webtools import RequestBuilder, PageOptions, WebLogger, Url
from rsshistory import ipc

sources = [
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCld68syR8Wi-GY_n4CaoJGA", "brodie robertson"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCROQqK3_z79JuTetNP3pIXQ", "captain midnight"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCTSRIY3GLFYIpkR2QwyeklA", "drew gooden"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCNnKprAG-MWLsk-GsbsC2BA", "flashgitz"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCRG_N2uO405WO4P3Ruef9NA", "friday checkout"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCR-DXc1voovS8nhAvccRZhg", "jeff gerling"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC7v3-2K1N84V67IF-WTRG-Q", "jeremy jahns"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC-2YHgc363EdcusLIBbgxzg", "joe scott"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCVIFCOJwv3emlVmBbPCZrvw", "joel havier"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCmGSJVG3mCRXVOP4yZrU1Dw", "john harris"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCLRlryMfL8ffxzrtqv0_k_w", "kino check"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCG2kQBVlgG7kOigXZTcKrQw", "kolem sie toczy"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCLr4hMhk_2KE0GUBSBrspGA", "kuba klawiter"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCNvzD7Z-g64bPXxGzaQaa4g", "gameranx"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw", "linus tech tips"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCl2mFZoRqjw_ELax4Yisf6w", "louis rossman"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC2eYFnH61tmytImy1mTYvhA", "luke smith"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCBJycsmduvYEL83R_U4JriQ", "marques brownlee"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCTTZqMWBvLsUYqYwKTdjvkw", "mateusz chrobok"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCswH8ovgUp5Bdg-0_JTYFNw", "russel brand"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCh9IfI45mmk59eDvSWtuuhQ", "ryan george"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCzKFvBRI6VT3jYJq6a820nA", "ryan long"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCA3-nIYWu4PTWkb6NwhEpzg", "ryan reynolds"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCyseFvMP4mZVlU5iEEbAamA", "salvatore ganacci"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCd6vEDS3SOhWbXZrxbrf_bw", "solid jj"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCD6VugMZKRhSyzWEWA9W2fg", "sssethtzeentach"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCDvZTWvHZPTxJ4K1yTD2a1g", "squidmar miniatures"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCtZO3K2p8mqFwiKWb9k7fXA", "techaltar"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCeeFfhMcJa1kjtfZAGskOCA", "techlinked"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCSJPFQdZwrOutnmSFYtbstA", "the critical drinker"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCDVb4m_5QHhZElT47E1oODg", "dave cullen show"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCSbdMXOI_3HGiFviLZO6kNA", "thrillseeker"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCxt2r57cLastdmrReiQJkEg", "tom nicolas"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCBa659QWEk1AI4Tg--mrJ2A", "tom scott"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCFLwN7vRu8M057qJF8TsBaA", "up is not down"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCxXu9tCU63mF1ntk89XPkzA", "worthkids"],
]


class ClientWebLogger(object):
    def info(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        print(detail_text)

    def debug(info_text, detail_text="", user=None, stack=False):
        #print(info_text)
        #print(detail_text)
        pass

    def warning(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        print(detail_text)

    def error(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        print(detail_text)

    def notify(info_text, detail_text="", user=None):
        print(info_text)
        print(detail_text)

    def exc(exception_object, info_text=None, user=None):
        print(str(exception_object))

        error_text = traceback.format_exc()
        print("Exception format")
        print(error_text)

        stack_lines = traceback.format_stack()
        stack_string = "".join(stack_lines)
        print("Stack:")
        print("".join(stack_lines))


def read_source(source):
    result = []

    RequestBuilder.crawling_server_port = 0
    RequestBuilder.crawling_headless_script = None
    RequestBuilder.crawling_full_script = None

    source_url = source[0]
    source_title = source[1]

    u = Url(source_url)
    response = u.get_response()

    if response:
        handler = u.get_handler()
        if handler.is_rss():
            for item in handler.p.get_container_elements():
                item["source"] = source_url
                item["source_title"] = source_title
                result.append(item)
        else:
            print("It is not RSS")
    else:
        print("Not response")

    return result


WebLogger.web_logger = ClientWebLogger


entries = []
for source in sources:
    print("Reading {}".format(source))
    source_entries = read_source(source)
    entries.extend(source_entries)

entries = sorted(entries, key = lambda x: x['date_published'], reverse=True)

for entry in entries:
    print("{} {} {} / {}".format(entry["date_published"], entry["link"], entry["title"], entry["source_title"]))
