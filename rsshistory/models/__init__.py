"""
Here only models should be.

When a model has too much code, some of it is moved to "controllers"
"""

from .system import (
    ConfigurationEntry,
    SystemOperation,
    UserConfig,
    AppLogging,
    AppLoggingController,
)
from .backgroundjob import (
    BackgroundJob,
    BackgroundJobHistory,
)
from .entries import (
    LinkDataModel,
    ArchiveLinkDataModel,
    BaseLinkDataModel,
    BaseLinkDataController,
)
from .sources import (
    SourceDataModel,
    SourceOperationalData,
    SourceCategories,
    SourceSubCategories,
)
from .export import (
    SourceExportHistory,
    DataExport,
)
from .domains import (
    Domains,
    DomainsSuffixes,
    DomainsTlds,
    DomainsMains,
)
from .keywords import (
    KeyWords,
)
from .entryrules import (
    EntryRules,
)
from .apikeys import (
    ApiKeys,
)
from .credentials import (
    Credentials,
)
from .useractions import (
    UserVotes,
    UserComments,
    UserBookmarks,
    UserTags,
    UserCompactedTags,
    CompactedTags,
    EntryCompactedTags,
)
from .userhistory import (
    UserSearchHistory,
    UserEntryVisitHistory,
    UserEntryTransitionHistory,
)
from .modelfiles import ModelFiles

from .readmarkers import ReadMarkers
from .readlater import ReadLater
from .browser import Browser

from .blockentry import BlockEntryList, BlockEntry, BlockListReader

from .gateway import Gateway

from .searchview import SearchView
