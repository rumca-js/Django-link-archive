from pathlib import Path
import subprocess
import shutil


class GitRepo(object):
    def __init__(self, git_data, timeout_s=60 * 60):
        self.git_data = git_data
        self.git_repo = git_data.remote_path
        self.timeout_s = timeout_s
        self.local_dir = self.calculate_local_dir()

    def get_local_dir(self):
        return self.local_dir

    def set_local_dir(self, adir):
        self.local_dir = adir

    def calculate_local_dir(self):
        last = self.get_repo_name()
        return Path(self.git_data.local_path) / last

    def up(self):
        git_path = Path(self.git_data.local_path)
        local = self.get_local_dir()

        if not local.is_dir():
            if not git_path.is_dir():
                git_path.mkdir(parents=True)
            self.clone()
        else:
            self.pull()

    def add(self, files):
        subprocess.run(
            ["git", "add", "-A"], cwd=self.get_local_dir(), timeout=self.timeout_s
        )

    def commit(self, commit_message):
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
        )

    def push(self):
        token = self.git_data.password
        user = self.git_data.user
        repo = self.get_repo_name()
        subprocess.run(
            [
                "git",
                "push",
                "https://{0}@github.com/{1}/{2}.git".format(token, user, repo),
            ],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
        )

    def get_repo_name(self):
        last = Path(self.git_repo).parts[-1]
        last = Path(last)
        last = last.stem
        return last


    def clone(self):
        subprocess.run(
            ["git", "clone", self.git_repo],
            cwd=self.git_data.local_path,
            timeout=self.timeout_s,
        )

    def pull(self):
        subprocess.run(
            ["git", "pull"], cwd=self.get_local_dir(), timeout=self.timeout_s
        )

    def copy_tree(self, input_path):
        expected_dir = self.get_local_dir()

        shutil.copytree(input_path, expected_dir, dirs_exist_ok=True)
