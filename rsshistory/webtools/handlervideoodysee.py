from .defaulturlhandler import DefaultUrlHandler


class OdyseeVideoHandler(DefaultUrlHandler):
    def __init__(self, url=None, contents=None, page_options=None):
        super().__init__(url, contents=contents, page_options=page_options)
        self.url = self.input2url(url)

    def is_handled_by(self):
        if not self.url:
            return

        from .url import Url

        protocol_less = Url.get_protololless(self.url)

        if protocol_less.startswith("odysee.com/@"):
            wh1 = protocol_less.find("@")
            wh2 = protocol_less.find("/", wh1 + 1)
            if wh2 >= 0:
                return True

    def input2url(self, url):
        from .url import Url

        protocol_less = Url.get_protololless(self.url)

        if protocol_less.startswith("odysee.com/@"):
            lines = protocol_less.split("/")
            if len(lines) < 3:
                return

            first = lines[0] # odysee.com
            self.channel = lines[1]
            self.video = lines[2]
            wh = self.video.find("?")
            if wh >= 0:
                self.video = self.video[:wh]

            protocol_less = "/".join([first,self.channel,self.video])

            return "https://" + protocol_less

    def get_video_code(self):
        return self.video

    def get_channel_code(self):
        return self.channel

    def get_link_classic(self):
        return "https://odysee.com/{}/{}".format(
            self.get_channel_code(), self.get_video_code()
        )

    def get_link_embed(self):
        return "https://odysee.com/$/embed/{0}".format(self.get_video_code())

    def get_response(self):
        from .url import Url
        from .handlerhttppage import HttpPageHandler

        if self.response:
            return self.response

        self.handler = Url(self.url, handler_class=HttpPageHandler)
        self.response = self.handler.get_response()

        if self.response:
            return self.response

    def get_feeds(self):
        from .handlerchannelodysee import OdyseeChannelHandler
        return [OdyseeChannelHandler().code2feed(self.channel)]
