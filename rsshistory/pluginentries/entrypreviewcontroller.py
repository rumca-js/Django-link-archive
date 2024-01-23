from ..webtools import HtmlPage

from .urlhandler import UrlHandler

from .entryyoutubeplugin import EntryYouTubePlugin
from .entryodyseeplugin import EntryOdyseePlugin
from .entrygenericplugin import EntryGenericPlugin


class EntryPreviewController(object):
    """
    Builds widget plugin.
    Only videos are displayed differently - we have preview for them

    TODO streamable?
    """

    def get(entry, user=None):
        h = UrlHandler.get(entry.link)

        if type(h) is UrlHandler.youtube_video_handler:
            return EntryYouTubePlugin(entry, user)

        if type(h) is UrlHandler.odysee_video_handler:
            return EntryOdyseePlugin(entry, user)

        return EntryGenericPlugin(entry, user)
