from .sourceparseplugin import BaseParsePlugin
from .sourcerssplugin import BaseRssPlugin
from .sourcecodeprojectplugin import CodeProjectPlugin
from .sourceinstalkiplugin import InstalkiPlugin
from .sourceniezaleznaplugin import NiezaleznaPlugin
from .sourcetvn24plugin import TVN24Plugin
from .sourcespotifyplugin import SpotifyPlugin


class SourceControllerBuilder(object):
    plugins = [
        CodeProjectPlugin,
        InstalkiPlugin,
        NiezaleznaPlugin,
        TVN24Plugin,
        SpotifyPlugin,
    ]

    def get(source):
        from ..models import SourceDataModel

        for plugin_def in SourceControllerBuilder.plugins:
            plugin = plugin_def(source)
            if source.source_type == plugin.PLUGIN_NAME:
                return plugin

        if source.source_type == SourceDataModel.SOURCE_TYPE_RSS:
            return BaseRssPlugin(source)
        elif source.source_type == SourceDataModel.SOURCE_TYPE_PARSE:
            return BaseParsePlugin(source)
        else:
            raise NotImplementedError(
                "Source: {}: Unsupported source type: {}".format(
                    source.title, source.source_type
                )
            )