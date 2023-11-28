from .sourcerssplugin import BaseRssPlugin
from .sourceparseplugin import BaseParsePlugin
from .sourcegenerousparserplugin import SourceGenerousParserPlugin
from .domainparserplugin import DomainParserPlugin

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
            raise NotImplementedError(
                "Source URL: {}: No such source".format(source_url)
            )

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
