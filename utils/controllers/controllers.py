class GenericEntryController(object):
    def __init__(self, entry, console=False):
        self.entry = entry
        self.console_printer = console

    def get_title(self, full_title=False):
        if not self.entry.title:
            return

        if not full_title:
            title = self.entry.title[:100]
        else:
            title = self.entry.title

        bracket_text = self.get_bracket_text()
        code = self.get_title_info_string()

        if code:
            title = "[{}] {}".format(code, title)

        if bracket_text:
            title = "[{}] {}".format(bracket_text, title)

        return title

    def get_bracket_text(self):
        id = self.entry.id
        votes = self.entry.page_rating_votes
        contents = self.entry.page_rating_contents

        text = ""

        if self.console_printer:
            text += str(id)

        if votes > 0:
            if text != "":
                text += "|"
            text += "{}".format(votes)

        #if contents:
        #    if text != "":
        #        text += "|"
        #    text += "{} ".format(contents)

        return text

    def get_title_info_string(self):
        code = ""
        if self.is_dead():
            code += "D"
        if self.entry.age != 0 and self.entry.age is not None:
            code += "A"
        if self.entry.page_rating_votes < 0:
            code += "V"

        if self.console_printer:
            if self.entry.bookmarked:
                code += "B"

        return code

    def is_dead(self):
        """
        We do not have to make elaborate checks for statuses and manual statuses.
        If there is a dead date -> it is dead. Period.
        """
        return self.entry.date_dead_since is not None
