from .baseplugin import BasePlugin


class TVN24Plugin(BasePlugin):
    def __init__(self):
        super().__init__()

    def get_address(self):
        return "https://tvn24.pl"

    def is_link_valid(self, address):
        if address.find("TVN24-po-ukrainsku") >= 0:
            return False
        return True
