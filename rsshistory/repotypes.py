import shutil

from .services.gitrepo import GitRepo


class DefaultRepo(GitRepo):
    def __init__(self, git_data):
        super().__init__(git_data)
