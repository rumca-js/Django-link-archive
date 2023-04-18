
class SourceHandler(object):
    def __init__(self, source_obj):
        self.source_obj = source_obj

    def is_youtube(self):
        return self.source_obj.url.find("https://www.youtube.com/feeds") >= 0
