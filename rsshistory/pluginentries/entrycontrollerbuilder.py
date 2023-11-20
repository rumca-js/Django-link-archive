class EntryControllerBuilder(object):
    def get(entry):
        from ..webtools import Page

        p = Page(entry.link)
        if p.is_youtube():
            from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

            handler = YouTubeLinkHandler(entry.link)
            if handler.get_video_code():
                from .entryyoutubeplugin import EntryYouTubePlugin

                return EntryYouTubePlugin(entry)

        from .entrygenericplugin import EntryGenericPlugin

        return EntryGenericPlugin(entry)
