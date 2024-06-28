"""
By default includes everything that extends behavior.
We can add different site mechanisms, handlers, controllers.
"""
from .sourcerssplugin import BaseRssPlugin
from .sourceparseplugin import BaseParsePlugin
from .sourceparseinternallinks import SourceParseInternalLinks
from .domainparserplugin import DomainParserPlugin
from .sourcejsonplugin import BaseSourceJsonPlugin
from .sourcegenericplugin import SourceGenericPlugin

from .sourceparseditigsplugin import SourceParseDigitsPlugin
from .codeprojectplugin import CodeProjectPlugin
from .tvn24plugin import TVN24Plugin
from .spotifyplugin import SpotifyPlugin
from .sourceyoutubechannel import YouTubePlugin
from .rssparserplugin import RssParserPlugin
from .hackernewsparserplugin import HackerNewsParserPlugin

from .sourcecontrollerbuilder import SourceControllerBuilder
