class LinkControllerBuilder(object):
    def get(entry):
        from ..webtools import Page

        p = Page(entry.link)
        if p.is_youtube():
            from .youtubelinkcontroller import YouTubeLinkController

            return YouTubeLinkController(entry)
        else:
            from .genericlinkcontroller import GenericLinkController

            return GenericLinkController(entry)
