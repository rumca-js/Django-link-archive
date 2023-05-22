from .youtubelinkhandler import YouTubeLinkHandler

class YouTubeLinkController(YouTubeLinkHandler):

    def __init__(self, entry):
        super().__init__(entry.link)
        self.entry = entry

    def get_menu_buttons(self):
        return []

    def get_frame_html(self):
        frame = self.get_frame()

        return """
    <div class="youtube_player_container">
       {}
    </div>""".format(frame)

    def get_description_html(self):
        frame = self.get_frame()

        return """{}""".format(self.entry.description)
