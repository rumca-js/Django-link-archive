from django.urls import reverse
from django.templatetags.static import static

from ...webtools import OdyseeVideoHandler

from ...apps import LinkDatabase
from ...models import ConfigurationEntry

from .entrygenericplugin import EntryGenericPlugin, EntryButton, EntryParameter


class EntryOdyseePlugin(EntryGenericPlugin):
    def __init__(self, entry, user=None):
        super().__init__(entry, user)

    def get_frame(self):
        h = OdyseeVideoHandler(self.entry.link)
        return """
        <iframe style="position: absolute; top: 0px; left: 0px; width: 100%; height: 100%;" width="100%" height="100%" src="{}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen"></iframe>
        """.format(
            h.get_link_embed()
        )

    def get_parameters(self):
        old_params = super().get_parameters()
        return old_params

    def get_frame_html(self):
        if not self.entry.is_user_appropriate(self.user):
            frame_text = """
            <div style="color:red">This material is restricted for age {}</div>"""

            frame_text = frame_text.format(self.entry.age)

            return frame_text
        else:
            frame_text = """
            <div class="youtube_player_container">
               {}
            </div>"""

            frame_inner = self.get_frame()

            frame_text = frame_text.format(frame_inner)

            return frame_text

    def get_edit_menu_buttons(self):
        buttons = super().get_edit_menu_buttons()
        return buttons

    def get_view_menu_buttons(self):
        buttons = super().get_view_menu_buttons()
        return buttons

    def get_advanced_menu_buttons(self):
        buttons = super().get_advanced_menu_buttons()
        return buttons
