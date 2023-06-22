class EntryControllerBuilder(object):
    def get(entry):
        from ..webtools import Page

        p = Page(entry.link)
        if p.is_youtube():
            from .entryyoutubeplugin import EntryYouTubePlugin

            return EntryYouTubePlugin(entry)
        else:
            from .entrygenericplugin import EntryGenericPlugin

            return EntryGenericPlugin(entry)
