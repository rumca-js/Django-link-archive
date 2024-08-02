from ..models import ModelFiles
from ..webtools import Url
from ..configuration import Configuration


class ModelFilesBuilder(object):
    def __init__(self):
        pass

    def build(self, file_name=None):
        if file_name is None:
            return
        if file_name == "":
            return

        c = Configuration.get_object().config_entry
        if not c.enabled_file_support:
            return

        p = Url(url=file_name)
        response = p.get_response()

        if not response:
            # consume
            return True

        contents = p.get_binary()

        if contents:
            if not ModelFiles.objects.filter(file_name=file_name).exists():
                ModelFiles.add(file_name, contents)
