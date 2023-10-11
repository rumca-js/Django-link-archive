from django.urls import reverse

from .youtubelinkhandler import YouTubeLinkHandler
from .entrygenericplugin import EntryGenericPlugin, EntryButton, EntryParameter
from ..apps import LinkDatabase


class EntryYouTubePlugin(YouTubeLinkHandler, EntryGenericPlugin):
    def __init__(self, entry):
        super().__init__(entry.link)
        self.entry = entry

    def get_menu_buttons(self):
        return [
            EntryButton(
                "Download music",
                reverse(
                    "{}:entry-download-music".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
            ),
            EntryButton(
                "Download video",
                reverse(
                    "{}:entry-download-video".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
            ),
            EntryButton(
                "Update link data",
                reverse(
                    "{}:entry-fix-youtube-details".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
            ),
            EntryButton(
                "YewTu.be",
                "https://yewtu.be/watch?v={}".format(self.get_video_code())
            ),
            EntryButton(
                "YouTube Music",
                "https://music.youtube.com/watch?v={}".format(self.get_video_code())
            ),
        ]

    def get_parameters(self):
        old_params = super().get_parameters()
        return old_params

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
        import re

        frame = self.get_frame()
        description = self.entry.description
        description = self.htmlify(description)

        return """{}""".format(description)
