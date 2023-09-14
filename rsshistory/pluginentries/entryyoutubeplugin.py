from django.urls import reverse

from .youtubelinkhandler import YouTubeLinkHandler
from .entrygenericplugin import EntryGenericPlugin, LinkButton
from ..apps import LinkDatabase


class EntryYouTubePlugin(YouTubeLinkHandler, EntryGenericPlugin):
    def __init__(self, entry):
        super().__init__(entry.link)
        self.entry = entry

    def get_menu_buttons(self):
        return [
            LinkButton(
                "Download music",
                reverse(
                    "{}:entry-download-music".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
            ),
            LinkButton(
                "Download video",
                reverse(
                    "{}:entry-download-video".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
            ),
            LinkButton(
                "Update link data",
                reverse(
                    "{}:entry-fix-youtube-details".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
            ),
        ]

    def get_frame_html(self):
        frame_text = """
        <div class="youtube_player_container">
           {}
        </div>"""

        if self.entry.age and self.entry.age >= 18:
            frame_text = """
            <div>
                <img src="{}" class="content-thumbnail"/>
            </div>"""

            frame_text = frame_text.format(self.entry.get_thumbnail())

            return frame_text
        else:
            frame_text = """
            <div class="youtube_player_container">
               {}
            </div>"""

            frame_inner = self.get_frame()

            frame_text = frame_text.format(frame_inner)

            return frame_text

    def get_description_html(self):
        frame = self.get_frame()

        return """{}""".format(self.entry.description)
