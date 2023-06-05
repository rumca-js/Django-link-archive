
from .baseplugin import BasePlugin
from .baseparseplugin import BaseParsePlugin
from .codeprojectplugin import CodeProjectPlugin
from .instalkiplugin import InstalkiPlugin
from .niezaleznaplugin import NiezaleznaPlugin
from .tvn24plugin import TVN24Plugin
from .spotifyplugin import SpotifyPlugin

class BasePluginBuilder(object):

    plugins = [CodeProjectPlugin,
               InstalkiPlugin,
               NiezaleznaPlugin,
               TVN24Plugin,
               SpotifyPlugin,
               ]

    def get(source):
        from ..models import SourceDataModel

        for plugin_def in BasePluginBuilder.plugins:
            plugin = plugin_def(source)
            if source.get_domain() == plugin.get_address():
                return plugin

        if source.source_type == SourceDataModel.SOURCE_TYPE_RSS:
            return BasePlugin(source)
        elif source.source_type == SourceDataModel.SOURCE_TYPE_PARSE:
            return BaseParsePlugin(source)
        else:
            raise NotImplemented("Unsupported source type: {}".format(source.source_type))
