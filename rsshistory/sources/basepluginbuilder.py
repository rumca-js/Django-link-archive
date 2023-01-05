
from .baseplugin import BasePlugin
from .codeprojectplugin import CodeProjectPlugin
from .instalkiplugin import InstalkiPlugin
from .niezaleznaplugin import NiezaleznaPlugin
from .tvn24plugin import TVN24Plugin

class BasePluginBuilder(object):

    plugins = [CodeProjectPlugin,
               InstalkiPlugin,
               NiezaleznaPlugin,
               TVN24Plugin]

    def get(name):
        for plugin_def in BasePluginBuilder.plugins:
            plugin = plugin_def()
            if name == plugin.get_address():
                return plugin

        return BasePlugin()
