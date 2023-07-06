from .sourceparseplugin import BaseParsePlugin
from .sourcerssplugin import BaseRssPlugin
from .sourcecodeprojectplugin import CodeProjectPlugin
from .sourceparseditigsplugin import SourceParseDigitsPlugin
from .sourcetvn24plugin import TVN24Plugin
from .sourcespotifyplugin import SpotifyPlugin
from .sourcegenerousparserplugin import SourceGenerousParserPlugin


class SourceControllerBuilder(object):
    plugins = [
        CodeProjectPlugin,
        SourceParseDigitsPlugin,
        TVN24Plugin,
        SpotifyPlugin,
        SourceGenerousParserPlugin
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
