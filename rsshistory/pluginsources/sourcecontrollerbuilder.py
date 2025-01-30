from .sourcerssplugin import BaseRssPlugin
from .sourceparseplugin import BaseParsePlugin
from .sourcejsonplugin import BaseSourceJsonPlugin

from .codeprojectplugin import CodeProjectPlugin
from .tvn24plugin import TVN24Plugin
from .spotifyplugin import SpotifyPlugin
from .rssparserplugin import RssParserPlugin
from .hackernewsparserplugin import HackerNewsParserPlugin
from ..models import AppLogging


class SourceControllerBuilder(object):
    plugins = [
        BaseRssPlugin,
        BaseParsePlugin,
        BaseSourceJsonPlugin,
        # domain specific
        CodeProjectPlugin,
        TVN24Plugin,
        SpotifyPlugin,
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

        AppLogging.notify(
            "Incorrectly configured source, ID:{} title:{}, type:{}. Setting it to base RSS type".format(
                source.id, source.title, source.source_type
            )
        )

        source.source_type = "BaseRssPlugin"
        source.save()

    def get_plugin_names():
        result = set()
        for plugin_def in SourceControllerBuilder.plugins:
            result.add(plugin_def.PLUGIN_NAME)

        return list(result)
