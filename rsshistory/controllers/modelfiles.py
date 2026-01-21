from ..models import ModelFiles
from ..configuration import Configuration


class ModelFilesBuilder(object):
    def __init__(self):
        pass

    def build(self, file_name=None):
        from ..pluginurl import UrlHandler

        if file_name is None:
            return
        if file_name == "":
            return

        c = Configuration.get_object().config_entry
        if not c.enabled_file_support:
            return

        p = UrlHandler(url=file_name)
        response = p.get_response()
        if response:
            binary_data = response.get_binary()
            if not binary_data:
                # consume
                return True

            if not ModelFiles.objects.filter(file_name=file_name).exists():
                ModelFiles.add(file_name, binary_data)
