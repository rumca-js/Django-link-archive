
class RequestsObject(object):
    def __init__(self, url, headers, timeout):
        self.status_code = 200
        self.apparent_encoding = "utf-8"
        self.encoding = "utf-8"

        if url == "https://test-with-proper-html.com":
            self.text = "text"
            self.content = "text"

        self.text = "text"
        self.content = "text"


class WebPageDisabled(object):
    def get_contents_function(self, url, headers, timeout):
        print("Mocked Requesting page: {}".format(url))
        return RequestsObject(url, headers, timeout)

    def disable_web_pages(self):
        from ..webtools import BasePage, HtmlPage

        BasePage.get_contents_function = self.get_contents_function
        HtmlPage.get_contents_function = self.get_contents_function
