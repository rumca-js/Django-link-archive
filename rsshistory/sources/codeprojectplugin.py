from .baseplugin import BasePlugin


class CodeProjectPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.allow_adding_with_current_time = True

    def get_address(self):
        return "https://www.codeproject.com"

    def get_feed_entry_map(self, source, feed_entry):
        output_map = BasePlugin.get_feed_entry_map(self, source, feed_entry)

        if 'href' in feed_entry.source:
            output_map['link'] = feed_entry.source['href']
            if output_map['link'].strip() == "":
                output_map['link'] = feed_entry.link
        else:
            output_map['link'] = feed_entry.link

        return output_map
