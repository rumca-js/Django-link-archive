from .models import AppLogging, DataExport
from .services.gitrepo import GitRepo


class DefaultRepo(GitRepo):
    def __init__(self, git_data):
        super().__init__(git_data)


class RepoFactory(object):
    def get(export_data):
        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            return GitRepo

        # TODO add support for more repo types. SMB?
