from ...webtools import Url

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
        h = Url.get_type(entry.link)

        if type(h) is Url.youtube_video_handler:
            return EntryYouTubePlugin(entry, user)

        if type(h) is Url.odysee_video_handler:
            return EntryOdyseePlugin(entry, user)

        return EntryGenericPlugin(entry, user)
