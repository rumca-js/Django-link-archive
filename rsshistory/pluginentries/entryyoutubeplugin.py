from django.urls import reverse
from django.templatetags.static import static

from .handlervideoyoutube import YouTubeVideoHandler
from .entrygenericplugin import EntryGenericPlugin, EntryButton, EntryParameter
from ..apps import LinkDatabase
from ..models import ConfigurationEntry


class EntryYouTubePlugin(EntryGenericPlugin):
    def __init__(self, entry, user = None):
        super().__init__(entry, user)

    def get_menu_buttons(self):
        return [
            EntryButton(
                self.user,
                "YouTube Props",
                reverse("{}:show-youtube-link-props".format(LinkDatabase.name))
                + "?page={}".format(self.entry.link),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
            ),
            EntryButton(
                self.user,
                "Music",
                reverse(
                    "{}:entry-download-music".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
            EntryButton(
                self.user,
                "Video",
                reverse(
                    "{}:entry-download-video".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
            EntryButton(
                self.user,
                "Invidious",
                "https://yewtu.be/watch?v={}".format(self.get_video_code()),
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "https://invidious.io/favicon-32x32.png",
            ),
            EntryButton(
                self.user,
                "YouTube Music",
                "https://music.youtube.com/watch?v={}".format(self.get_video_code()),
                ConfigurationEntry.ACCESS_TYPE_ALL,
                static(
                    "{}/icons/icons8-youtube-music-96.png".format(LinkDatabase.name)
                ),
            ),
            EntryButton(
                self.user,
                "Update link data",
                reverse(
                    "{}:entry-fix-youtube-details".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
            ),
        ]

    def get_video_code(self):
        h = YouTubeVideoHandler(self.entry.link)
        return h.get_video_code()

    def get_frame(self):
        h = YouTubeVideoHandler(self.entry.link)
        return '<iframe src="{0}" frameborder="0" allowfullscreen class="youtube_player_frame"></iframe>'.format(
            h.get_link_embed()
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
