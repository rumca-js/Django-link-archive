from django.urls import reverse
from django.templatetags.static import static

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..pluginentries.urlhandler import UrlHandler

from .entrygenericplugin import EntryGenericPlugin, EntryButton, EntryParameter


class EntryYouTubePlugin(EntryGenericPlugin):
    def __init__(self, entry, user=None):
        super().__init__(entry, user)

    def get_menu_buttons(self):
        return []

    def get_edit_menu_buttons(self):
        buttons = super().get_edit_menu_buttons()

        buttons.append(
            EntryButton(
                self.user,
                "Music",
                reverse(
                    "{}:entry-download-music".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Downloads YouTube music",
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
        )
        buttons.append(
            EntryButton(
                self.user,
                "Video",
                reverse(
                    "{}:entry-download-video".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Downloads YouTube video",
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "Update link data",
                reverse(
                    "{}:entry-fix-youtube-details".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Updates link data",
            ),
        )

        return buttons

    def get_view_menu_buttons(self):
        buttons = super().get_view_menu_buttons()

        buttons.append(
            EntryButton(
                self.user,
                "YouTube Music",
                "https://music.youtube.com/watch?v={}".format(self.get_video_code()),
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Link to YouTube music",
                static(
                    "{}/icons/icons8-youtube-music-96.png".format(LinkDatabase.name)
                ),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "Invidious",
                "https://yewtu.be/watch?v={}".format(self.get_video_code()),
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Link to Invidious instance",
                "https://invidious.io/favicon-32x32.png",
            ),
        )

        return buttons

    def get_advanced_menu_buttons(self):
        buttons = super().get_advanced_menu_buttons()
        return buttons

    def get_video_code(self):
        h = UrlHandler.get(self.entry.link)
        return h.get_video_code()

    def get_frame(self):
        """
        @note Some YouTube videos will not play without referrerpolicy.
        """

        h = UrlHandler.get(self.entry.link)
        return '<iframe src="{0}" frameborder="0" allowfullscreen class="youtube_player_frame" referrerpolicy="no-referrer-when-downgrade"></iframe>'.format(
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
