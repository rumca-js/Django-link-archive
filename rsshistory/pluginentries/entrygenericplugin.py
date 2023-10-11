class EntryButton(object):
    def __init__(self, name, action):
        self.name = name
        self.action = action


class EntryParameter(object):
    def __init__(self, name, description):
        self.name = name
        self.description = description


class EntryGenericPlugin(object):
    def __init__(self, entry):
        self.entry = entry

    def get_menu_buttons(self):
        return []

    def get_parameters(self):
        parameters = []

        parameters.append(EntryParameter("Url", '<a href="{}">{}</a>'.format(self.entry.link, self.entry.link)))

        parameters.append(EntryParameter("Publish date", self.entry.date_published))
        parameters.append(EntryParameter("Artist", self.entry.artist))
        parameters.append(EntryParameter("Album", self.entry.album))
        if self.entry.user:
            parameters.append(EntryParameter("User", self.entry.user))
        parameters.append(EntryParameter("Vote", self.entry.get_vote()))
        parameters.append(EntryParameter("Language", self.entry.language))
        if self.entry.dead:
            parameters.append(EntryParameter("Dead", self.entry.dead))

        return parameters

    def get_frame_html(self):
        return ""

    def get_description_html(self):
        description = self.entry.description

        return """{}""".format(self.htmlify(description))

    def htmlify(self, description):
        import re

        #inside = 0
        #for index, letter in enumerate(description):
        #    if letter == "<":
        #        inside += 1
        #    if letter == ">":
        #        inside -= 1

        #    if description[index:index+4] == "http":
        #        links = re.findall("(https?://[a-zA-Z0-9./\-_]+)", description)
        #        for link in links:
        #            description = description.replace(link, '<a href="{}">{}</a>'.format(link, link))

        return description
