from .models import AppLogging, DataExport
from .services.gitrepository import GitRepository
from .repositoryinterface import RepositoryInterface


class RepositoryFactory(object):
    def get(export_data):
        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            return GitRepository

        elif export_data.export_type == DataExport.EXPORT_TYPE_LOC:
            return RepositoryInterface

        else:
            raise NotImplementedError("Not implemented export type")
