"""
Simple scraping script.
"""
import socket
import json
import traceback
import asyncio
import time
import requests

from webtools import (
   Url,
   fetch_url,
   fetch_all_urls,
   WebConfig,
   HttpPageHandler,
)


__version__ = "0.0.1"


async def main():
    WebConfig.use_print_logging()

    # TODO - there seems to be some problems with feedparser, when used with asyncio threads
    # module 'xml.sax.expatreader' has no attribute 'create_parser'

    links = [
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCXGgrKt94gR6lmN4aN3mYTg",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCyl5V3-J_Bsy3x-EBCJwepg",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCmrLCXSDScliR7q8AxxjvXg",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UC7vVhkEfw4nOGp8TyDk7RcQ",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UClozNP-QPyVatzpGKC25s0A",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCld68syR8Wi-GY_n4CaoJGA",
        "https://www.youtube.com/feeds/videos.xml?channel_id=UCROQqK3_z79JuTetNP3pIXQ",
            ]

    results = await fetch_all_urls(links)
    for result in results:
        response = result.get_response()
        print("{} {}".format(response.url, response.status_code))


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print(f"Done in {time.time() - start_time} seconds")
