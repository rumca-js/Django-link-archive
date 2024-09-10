from webtools import DomainAwarePage, HttpPageHandler, RssPage, Url

class OpenRss(object):
    def __init__(self, url):
        self.url = url

    def find_rss_link(self):
        p = DomainAwarePage(self.url)
        url_procolles = p.get_protocolless()

        options = Url.get_url_options(self.url) 
        options.use_headless_browser = False
        options.use_full_browser = False
        options.use_browser_promotions = False

        u = Url("https://openrss.org/" + url_procolles, page_options = options)
        u.get_response()

        handler = u.get_handler()
        if type(handler) is HttpPageHandler:
            if type(handler.p) is RssPage:
                return handler.p.get_link()
