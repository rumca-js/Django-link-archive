from django.urls import reverse

from .youtubelinkhandler import YouTubeLinkHandler
from .genericlinkcontroller import GenericLinkController, LinkButton

class YouTubeLinkController(YouTubeLinkHandler, GenericLinkController):

    def __init__(self, entry):
        super().__init__(entry.link)
        self.entry = entry

    def get_menu_buttons(self):
        return [LinkButton("Download music", reverse('rsshistory:entry-download-music', args=[self.entry.id])),
                LinkButton("Download video", reverse('rsshistory:entry-download-video', args=[self.entry.id])),
                LinkButton("Fix YouTube properties", reverse('rsshistory:entry-fix-youtube-details', args=[self.entry.id])),]

    def get_frame_html(self):
        frame = self.get_frame()

        return """
    <div class="youtube_player_container">
       {}
    </div>""".format(frame)

    def get_description_html(self):
        frame = self.get_frame()

        return """{}""".format(self.entry.description)
