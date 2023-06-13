from pathlib import Path
import subprocess

"""
repo_dir = 'mathematics'

repo = Repo(repo_dir)
file_list = [
    'numerical_analysis/regression_analysis/simple_regression_analysis.py',
    'numerical_analysis/regression_analysis/simple_regression_analysis.png'
]
commit_message = 'Add simple regression analysis'

repo.index.add(file_list)
repo.index.commit(commit_message)

origin = repo.remote('origin')
origin.push()
"""


class GitRepo(object):
    def __init__(self, git_data, git_repo):
        self.git_data = git_data
        self.git_repo = git_repo

    def up(self):
        git_path = Path(self.git_data.git_path)
        local = self.get_local_dir()

        if not local.is_dir():
            if not git_path.is_dir():
                git_path.mkdir(parents=True)
            self.clone()
        else:
            self.pull()

    def add(self, files):
        subprocess.run(['git', 'add', '-A'], cwd=self.get_local_dir())
        # self.git.index.add(files)

    def commit(self, commit_message):
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=self.get_local_dir())
        # self.git.index.commit(commit_message)

    def push(self):
        token = self.git_data.git_token
        user = self.git_data.git_user
        repo = self.get_repo_name()
        subprocess.run(['git', 'push', 'https://{0}@github.com/{1}/{2}.git'.format(token, user, repo)],
                       cwd=self.get_local_dir())
        # origin = self.git.remote('origin')
        # origin.push()

    def get_repo_name(self):
        last = Path(self.git_repo).parts[-1]
        last = Path(last)
        last = last.stem
        return last

    def get_local_dir(self):
        last = self.get_repo_name()

        return Path(self.git_data.git_path) / last

    def clone(self):
        subprocess.run(['git', 'clone', self.git_repo], cwd=self.git_data.git_path)

    def pull(self):
        subprocess.run(['git', 'pull'], cwd=self.get_local_dir())
