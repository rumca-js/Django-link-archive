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
        SourceGenerousParserPlugin,
    ]

    def get(source_url):
        from ..models import SourceDataModel

        sources = SourceDataModel.objects.filter(url = source_url)
        if len(sources) == 0:
            raise NotImplementedError(
                "Source URL: {}: No such source".format(
                    source_url
                )
            )

        source = sources[0]
        # database operations should be short lived. we do not pass source object.
            
        for plugin_def in SourceControllerBuilder.plugins:
            plugin = plugin_def(source.id)
            if source.source_type == plugin.PLUGIN_NAME:
                return plugin

        if source.source_type == SourceDataModel.SOURCE_TYPE_RSS:
            return BaseRssPlugin(source.id)
        elif source.source_type == SourceDataModel.SOURCE_TYPE_PARSE:
            return BaseParsePlugin(source.id)
        else:
            raise NotImplementedError(
                "Source:{}: Unsupported source type:{}".format(
                    source.title, source.source_type
                )
            )
