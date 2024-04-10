from .sourcerssplugin import BaseRssPlugin


class CodeProjectPlugin(BaseRssPlugin):
    PLUGIN_NAME = "CodeProjectPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)
        self.allow_adding_with_current_time = True

    def enhance(self, props):
        """
        TODO unused?
        """
        feed_entry = props["feed_entry"]

        props = super().enhance(props)

        if "href" in feed_entry.source:
            props["link"] = feed_entry.source["href"]
            if props["link"].strip() == "":
                props["link"] = feed_entry.link
        else:
            props["link"] = feed_entry.link

        if props["link"].endswith("/"):
            props["link"] = props["link"][:-1]

        return props
