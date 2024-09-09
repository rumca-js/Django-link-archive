from utils.services.gitrepository import GitRepository
from utils.repositoryinterface import RepositoryInterface

from .models import AppLogging, DataExport


class RepositoryFactory(object):
    def get(export_data):
        if export_data.export_type == DataExport.EXPORT_TYPE_GIT:
            return GitRepository

        elif export_data.export_type == DataExport.EXPORT_TYPE_LOC:
            return RepositoryInterface

        else:
            raise NotImplementedError("Not implemented export type")
