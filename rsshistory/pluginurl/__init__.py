"""
This module should include every special handling for URLs, from various services

By default includes everything that extends behavior.
We can add different site mechanisms, handlers, controllers.
"""

from .handlervideoyoutube import YouTubeVideoHandler, YouTubeJsonHandler
from .handlerchannelyoutube import YouTubeChannelHandler
from .urlhandler import UrlHandler, UrlPropertyValidator, UrlAgeModerator
from .entryurlinterface import EntryUrlInterface
