from .handlerchannelyoutube import YouTubeSourceHandler
from .handlerchannelodysee import OdyseeSourceHandler


class DefaultHandler(object):
    def __init__(self, url):
        self.url = url

    def get_channel_url(self):
        return self.url


class ChannelHandler(object):
    def get(url):
        supported = ChannelHandler.get_supported(url)
        if supported:
            return supported

        if not supported:
            return DefaultHandler(url)

    def get_supported(url):
        if url.find("youtube.com") >= 0:
            return YouTubeSourceHandler(url)
        if url.find("odysee.com") >= 0:
            return OdyseeSourceHandler(url)
