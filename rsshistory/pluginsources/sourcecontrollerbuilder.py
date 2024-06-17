from .sourcerssplugin import BaseRssPlugin
from .sourceparseplugin import BaseParsePlugin
from .sourceparseinternallinks import SourceParseInternalLinks
from .domainparserplugin import DomainParserPlugin
from .sourcejsonplugin import BaseSourceJsonPlugin

from .sourceparseditigsplugin import SourceParseDigitsPlugin
from .codeprojectplugin import CodeProjectPlugin
from .tvn24plugin import TVN24Plugin
from .spotifyplugin import SpotifyPlugin
from .sourceyoutubechannel import YouTubePlugin
from .rssparserplugin import RssParserPlugin
from .hackernewsparserplugin import HackerNewsParserPlugin


class SourceControllerBuilder(object):
    plugins = [
        BaseRssPlugin,
        BaseParsePlugin,
        SourceParseInternalLinks,
        DomainParserPlugin,
        BaseSourceJsonPlugin,
        # domain specific
        SourceParseDigitsPlugin,
        CodeProjectPlugin,
        TVN24Plugin,
        SpotifyPlugin,
        YouTubePlugin,
        RssParserPlugin,
        HackerNewsParserPlugin,
    ]

    def get(source_id):
        from ..models import SourceDataModel

        sources = SourceDataModel.objects.filter(id=source_id)
        if len(sources) == 0:
            return None

        source = sources[0]
        # database operations should be short lived. we do not pass source object.

        for plugin_def in SourceControllerBuilder.plugins:
            plugin = plugin_def(source_id)
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
