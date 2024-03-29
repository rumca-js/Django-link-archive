from pathlib import Path
import subprocess
import shutil


class GitRepo(object):
    def __init__(self, git_data, timeout_s=60 * 60):
        self.git_data = git_data
        self.git_repo = git_data.remote_path
        self.timeout_s = timeout_s
        self.operating_dir = self.git_data.local_path

    def get_local_dir(self):
        """
        TODO rename to repo dir
        """
        last = self.get_repo_name()
        return self.operating_dir / last

    def set_operating_dir(self, adir):
        """
        TODO rename to cwd dir
        """
        self.operating_dir = Path(adir)

    def get_operating_dir(self):
        return Path(self.operating_dir)

    def up(self):
        cwd = self.get_operating_dir()
        local = self.get_local_dir()

        print("Local:{}\ncwd:{}\n".format(local, cwd))

        if not cwd.is_dir():
            cwd.mkdir(parents=True)

        if not local.is_dir():
            self.clone()
        else:
            self.pull()

    def add(self, files):
        p = subprocess.run(
            ["git", "add", "-A"], cwd=self.get_local_dir(), timeout=self.timeout_s
        )
        p.check_returncode()

    def commit(self, commit_message):
        p = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
        )
        if p.returncode != 0:
            raise IOError("Invalid git return code for add")

    def push(self):
        token = self.git_data.password
        user = self.git_data.user
        repo = self.get_repo_name()
        p = subprocess.run(
            [
                "git",
                "push",
                "https://{0}@github.com/{1}/{2}.git".format(token, user, repo),
            ],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
        )
        p.check_returncode()

    def get_repo_name(self):
        last = Path(self.git_repo).parts[-1]
        last = Path(last)
        last = last.stem
        return last

    def clone(self):
        p = subprocess.run(
            ["git", "clone", self.git_repo],
            cwd=self.get_operating_dir(),
            timeout=self.timeout_s,
        )
        p.check_returncode()

    def pull(self):
        print("Pulling from directory: {}".format(self.get_local_dir()))
        p = subprocess.run(
            ["git", "pull"], cwd=self.get_local_dir(), timeout=self.timeout_s
        )
        p.check_returncode()

    def copy_tree(self, input_path):
        expected_dir = self.get_local_dir()

        shutil.copytree(input_path, expected_dir, dirs_exist_ok=True)
