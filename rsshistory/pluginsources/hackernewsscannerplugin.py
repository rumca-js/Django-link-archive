import os
import re

from ..models import UserTags
from ..configuration import Configuration
from .sourcerssplugin import BaseRssPlugin
from .rssscannerplugin import RssScannerPlugin

from ..webtools import ContentLinkParser, HtmlPage, BasePage


class HackerNewsScannerPlugin(RssScannerPlugin):
    """
    - We read RSS
    - For each item in RSS we find internal links for this source
    - For each internal link, we read page, and try to add links from inside
    """

    PLUGIN_NAME = "HackerNewsScannerPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def is_internal_page_processed(self, url):
        url_page = BasePage(url)

        return url_page.get_domain().find("news.ycombinator.com") >= 0
