
class LinkHandlerBuilder(object):

   def get_handler(url):
      from ..webtools import Page
      p = Page(url)
      dom = str(p.get_domain_only())
      if dom.startswith("youtube") or dom.startswith("m.youtube"):
         from .youtubelinkhandler import YouTubeLinkHandler
         return YouTubeLinkHandler(url)
