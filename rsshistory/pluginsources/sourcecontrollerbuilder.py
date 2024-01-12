from .sourcerssplugin import BaseRssPlugin
from .sourceparseplugin import BaseParsePlugin
from .sourcegenerousparserplugin import SourceGenerousParserPlugin
from .domainparserplugin import DomainParserPlugin
from .sourcejsonplugin import BaseSourceJsonPlugin

from .sourceparseditigsplugin import SourceParseDigitsPlugin
from .nownownowparserplugin import NowNowNowParserPlugin
from .searchmysiterssplugin import SearchMySiteRSSPlugin
from .codeprojectplugin import CodeProjectPlugin
from .tvn24plugin import TVN24Plugin
from .spotifyplugin import SpotifyPlugin


class SourceControllerBuilder(object):
    plugins = [
        BaseRssPlugin,
        BaseParsePlugin,
        SourceGenerousParserPlugin,
        DomainParserPlugin,
        BaseSourceJsonPlugin,
        # domain specific
        SourceParseDigitsPlugin,
        NowNowNowParserPlugin,
        SearchMySiteRSSPlugin,
        CodeProjectPlugin,
        TVN24Plugin,
        SpotifyPlugin,
    ]

    def get(source_url):
        from ..models import SourceDataModel

        sources = SourceDataModel.objects.filter(url=source_url)
        if len(sources) == 0:
            return None

        source = sources[0]
        # database operations should be short lived. we do not pass source object.

        for plugin_def in SourceControllerBuilder.plugins:
            plugin = plugin_def(source.id)
            if source.source_type == plugin.PLUGIN_NAME:
                return plugin

        raise NotImplementedError(
            "Source:{}: Unsupported source type:{}".format(
                source.title, source.source_type
            )
        )

    def get_plugin_names():
        result = set()
        for plugin_def in SourceControllerBuilder.plugins:
            result.add(plugin_def.PLUGIN_NAME)

        return list(result)
