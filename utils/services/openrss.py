from webtoolkit import UrlLocation, RssPage, RemoteUrl, HttpPageHandler


class OpenRss(object):
    def __init__(self, url):
        self.url = url

    def find_rss_link(self):
        p = UrlLocation(self.url)
        url_procolles = p.get_protocolless()

        u = RemoteUrl("", "https://openrss.org/" + url_procolles)
        u.get_response()

        handler = u.get_handler()
        if type(handler) is HttpPageHandler:
            if type(handler.p) is RssPage:
                return handler.p.get_link()
