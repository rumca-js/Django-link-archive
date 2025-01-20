"""
Similar project: https://pypi.org/project/abstract-webtools/
"""

from .webtools import *
from .pages import *
from .webconfig import WebConfig
from .urllocation import UrlLocation

from .url import (
    Url,
    DomainCache,
    DomainCacheInfo,
    fetch_url,
    fetch_all_urls,
)

from .handlerhttppage import (
    HttpRequestBuilder,
    HttpPageHandler,
)
from .handlers import (
    RedditChannelHandler,
    RedditUrlHandler,
    GitHubUrlHandler,
    ReturnDislike,
    HackerNewsHandler,
)

from .crawlers import (
    CrawlerInterface,
    RequestsCrawler,
    SeleniumChromeHeadless,
    SeleniumChromeFull,
    SeleniumUndetected,
    ScriptCrawler,
    StealthRequestsCrawler,
    RemoteServerCrawler,
    selenium_feataure_enabled,
    RemoteServer,
)
from .crawlerscript import (
    ScriptCrawlerParser,
    ScriptCrawlerInterface,
)

from .handlerchannelyoutube import YouTubeChannelHandler
from .handlervideoyoutube import YouTubeVideoHandler, YouTubeJsonHandler

from .handlerchannelodysee import OdyseeChannelHandler
from .handlervideoodysee import OdyseeVideoHandler

from .feedreader import FeedReader
from .feedclient import FeedClient, FeedClientParser

from .contentmoderation import (
    UrlPropertyValidator,
    UrlPropertyValidator,
    UrlAgeModerator,
)
