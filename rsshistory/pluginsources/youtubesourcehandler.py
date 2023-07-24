class YouTubeSourceHandler(object):
    def __init__(self, url=None):
        if url:
            self.url = YouTubeSourceHandler.input2url(url)

    def get_channel_code(self):
        return YouTubeSourceHandler.input2code(self.url)

    def input2url(item):
        code = YouTubeSourceHandler.input2code(item)
        return YouTubeSourceHandler.code2url(code)

    def code2url(code):
        return "https://www.youtube.com/channel/{}".format(code)

    def code2feed(code):
        return "https://www.youtube.com/feeds/videos.xml?channel_id={}".format(code)

    def input2code(url):
        wh = url.find("www.youtube.com")
        if wh == -1:
            return

        if url.find("/channel/") >= 0:
            return YouTubeSourceHandler.input2code_channel(url)
        if url.find("/feeds/") >= 0:
            return YouTubeSourceHandler.input2code_feeds(url)

    def input2code_channel(url):
        wh = url.rfind("/")
        return url[wh + 1 :]

    def input2code_feeds(url):
        wh = url.find("=")
        if wh >= 0:
            return url[wh + 1 :]
