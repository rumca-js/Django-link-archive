from webtoolkit import OdyseeVideoHandler, YouTubeVideoJsonHandler

from .entryyoutubeplugin import EntryYouTubePlugin
from .entryodyseeplugin import EntryOdyseePlugin
from .entrygenericplugin import EntryGenericPlugin


class EntryPreviewBuilder(object):
    """
    Builds widget plugin.
    Only videos are displayed differently - we have preview for them

    TODO streamable?
    TODO pass request instead of user
    """

    def get(entry, user=None):
        youtube_handler = YouTubeVideoJsonHandler(entry.link)
        if youtube_handler.is_handled_by():
            return EntryYouTubePlugin(entry, user)

        odysee_handler = OdyseeVideoHandler(entry.link)
        if odysee_handler.is_handled_by():
            return EntryOdyseePlugin(entry, user)

        return EntryGenericPlugin(entry, user)
