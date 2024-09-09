"""
Here only models should be.

When a model has too much code, some of it is moved to "controllers"
"""
from .system import (
    ConfigurationEntry,
    SystemOperation,
    UserConfig,
    AppLogging,
    BackgroundJob,
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
from .useractions import (
    UserTags,
    UserVotes,
    LinkCommentDataModel,
    UserBookmarks,
    CompactedTags,
)
from .userhistory import (
    UserSearchHistory,
    UserEntryVisitHistory,
    UserEntryTransitionHistory,
)
from .modelfiles import ModelFiles

from .readmarkers import ReadMarkers
