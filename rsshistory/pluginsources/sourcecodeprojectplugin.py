from .sourcerssplugin import BaseRssPlugin


class CodeProjectPlugin(BaseRssPlugin):
    PLUGIN_NAME = "CodeProjectPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)
        self.allow_adding_with_current_time = True

    def get_feed_entry_map(self, source, feed_entry):
        output_map = BaseRssPlugin.get_feed_entry_map(self, source, feed_entry)

        if "href" in feed_entry.source:
            output_map["link"] = feed_entry.source["href"]
            if output_map["link"].strip() == "":
                output_map["link"] = feed_entry.link
        else:
            output_map["link"] = feed_entry.link

        return output_map
