from ..webtools import HtmlPage


class EntryControllerBuilder(object):
    def get(entry, user=None):
        p = HtmlPage(entry.link)
        if p.is_youtube():
            from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

            handler = YouTubeVideoHandler(entry.link)
            if handler.get_video_code():
                from .entryyoutubeplugin import EntryYouTubePlugin

                return EntryYouTubePlugin(entry, user)

        if entry.link.find("odysee") >= 0:
            from .entryodyseeplugin import EntryOdyseePlugin

            return EntryOdyseePlugin(entry, user)

        from .entrygenericplugin import EntryGenericPlugin

        return EntryGenericPlugin(entry, user)
