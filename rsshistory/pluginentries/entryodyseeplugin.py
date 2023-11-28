from django.urls import reverse
from django.templatetags.static import static

from .handlervideoodysee import OdyseeVideoHandler
from .entrygenericplugin import EntryGenericPlugin, EntryButton, EntryParameter
from ..apps import LinkDatabase


class EntryOdyseePlugin(OdyseeVideoHandler, EntryGenericPlugin):
    def __init__(self, entry):
        super().__init__(entry.link)
        self.entry = entry

    def get_frame(self):
        return """
        <iframe style="position: absolute; top: 0px; left: 0px; width: 100%; height: 100%;" width="100%" height="100%" src="{}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; fullscreen">
        """.format(self.get_link_embed())

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
