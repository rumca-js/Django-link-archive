class LinkButton(object):
    def __init__(self, name, action):
        self.name = name
        self.action = action


class EntryGenericPlugin(object):
    def __init__(self, entry):
        self.entry = entry

    def get_menu_buttons(self):
        return []

    def get_frame_html(self):
        return ""

    def get_description_html(self):
        return """
       {}
    """.format(
            self.entry.description
        )
