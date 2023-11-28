class EntryControllerBuilder(object):
    def get(entry):
        from ..webtools import HtmlPage

        p = HtmlPage(entry.link)
        if p.is_youtube():
            from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

            handler = YouTubeVideoHandler(entry.link)
            if handler.get_video_code():
                from .entryyoutubeplugin import EntryYouTubePlugin

                return EntryYouTubePlugin(entry)

        if entry.link.find("odysee") >= 0:
            from .entryodyseeplugin import EntryOdyseePlugin

            return EntryOdyseePlugin(entry)

        from .entrygenericplugin import EntryGenericPlugin

        return EntryGenericPlugin(entry)
