from django.urls import reverse
from django.templatetags.static import static

from .handlervideoyoutube import YouTubeVideoHandler
from .entrygenericplugin import EntryGenericPlugin, EntryButton, EntryParameter
from ..apps import LinkDatabase


class EntryYouTubePlugin(YouTubeVideoHandler, EntryGenericPlugin):
    def __init__(self, entry):
        super().__init__(entry.link)
        self.entry = entry

    def get_menu_buttons(self):
        return [
            EntryButton(
                "YouTube Props",
                reverse(
                    "{}:show-youtube-link-props".format(LinkDatabase.name)
                ) + "?page={}".format(self.entry.link),
            ),
            EntryButton(
                "Music",
                reverse(
                    "{}:entry-download-music".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
            EntryButton(
                "Video",
                reverse(
                    "{}:entry-download-video".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
            EntryButton(
                "Invidious",
                "https://yewtu.be/watch?v={}".format(self.get_video_code()),
                "https://invidious.io/favicon-32x32.png",
            ),
            EntryButton(
                "YouTube Music",
                "https://music.youtube.com/watch?v={}".format(self.get_video_code()),
                static(
                    "{}/icons/icons8-youtube-music-96.png".format(LinkDatabase.name)
                ),
            ),
            EntryButton(
                "Update link data",
                reverse(
                    "{}:entry-fix-youtube-details".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
            ),
        ]

    def get_frame(self):
        return '<iframe src="{0}" frameborder="0" allowfullscreen class="youtube_player_frame"></iframe>'.format(
            self.get_link_embed()
        )

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

        description = self.entry.description
        description = self.htmlify(description)

        return """{}""".format(description)
