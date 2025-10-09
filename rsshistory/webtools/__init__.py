"""
Similar project: https://pypi.org/project/abstract-webtools/
"""

from .webtools import *
from .webconfig import WebConfig

from .url import (
    Url,
    DomainCache,
    DomainCacheInfo,
    fetch_url,
    fetch_all_urls,
)

from .handlers import (
    HttpRequestBuilder,
    HttpPageHandler,
    YouTubeChannelHandler,
    YouTubeVideoHandler,
    YouTubeJsonHandler,
    OdyseeChannelHandler,
    OdyseeVideoHandler,
    RedditUrlHandler,
    GitHubUrlHandler,
    ReturnDislike,
    HackerNewsHandler,
    InternetArchive,
    FourChanChannelHandler,
    TwitterUrlHandler,
)

from .crawlers import (
    CrawlerInterface,
    RequestsCrawler,
    SeleniumDriver,
    SeleniumChromeHeadless,
    SeleniumChromeFull,
    SeleniumUndetected,
    ScriptCrawler,
    StealthRequestsCrawler,
)
from .crawlerscript import (
    ScriptCrawlerParser,
)
