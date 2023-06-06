
from .baseplugin import BasePlugin
from .baseparseplugin import BaseParsePlugin
from .baserssplugin import BaseRssPlugin
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
            if source.source_type == plugin.PLUGIN_NAME:
                return plugin

        if source.source_type == SourceDataModel.SOURCE_TYPE_RSS:
            return BaseRssPlugin(source)
        elif source.source_type == SourceDataModel.SOURCE_TYPE_PARSE:
            return BaseParsePlugin(source)
        else:
            raise NotImplementedError("Source: {}: Unsupported source type: {}".format(source.title, source.source_type))
