from .baseplugin import BasePlugin


class TVN24Plugin(BasePlugin):
    def __init__(self, source):
        super().__init__(source)

    def get_address(self):
        return "https://tvn24.pl"

    def is_link_valid(self, address):
        if address.find("TVN24-po-ukrainsku") >= 0:
            return False
        return True
