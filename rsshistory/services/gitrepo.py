from pathlib import Path
import subprocess
import shutil
from ..models import AppLogging


class GitRepo(object):
    def __init__(self, git_data, timeout_s=60 * 60):
        self.git_data = git_data
        self.git_repo = git_data.remote_path
        self.timeout_s = timeout_s
        self.operating_dir = self.git_data.local_path
        self.is_different_flag = None

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

        if not cwd.is_dir():
            cwd.mkdir(parents=True)

        if not local.is_dir():
            self.clone()
        else:
            self.revert_all_changes()
            self.pull()

    def add(self, files):
        p = subprocess.run(
            ["git", "add", "-A"],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
            capture_output=True,
        )
        self.check_process(p)

    def commit(self, commit_message):
        self.is_different_flag = self.is_different()
        if not self.is_different_flag:
            return

        p = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
            capture_output=True,
        )
        self.check_process(p)

    def push(self):
        if not self.is_different_flag:
            return

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
            capture_output=True,
        )
        self.check_process(p)

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
            capture_output=True,
        )
        self.check_process(p)

    def is_different(self):
        p = subprocess.run(
            ["git", "diff", "--exit-code"],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
            capture_output=True,
        )
        if p.returncode == 0:
            return False

        return True

    def revert_all_changes(self):
        p = subprocess.run(
            ["git", "checkout", "."],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
            capture_output=True,
        )
        self.check_process(p)

    def pull(self):
        p = subprocess.run(
            ["git", "pull"],
            cwd=self.get_local_dir(),
            timeout=self.timeout_s,
            capture_output=True,
        )
        self.check_process(p)

    def copy_tree(self, input_path):
        expected_dir = self.get_local_dir()

        shutil.copytree(input_path, expected_dir, dirs_exist_ok=True)

    def check_process(self, p):
        if p.returncode != 0:
            AppLogging.error(
                "GIT status:{}\nstdout:{}\nstderr:{}".format(
                    p.returncode, p.stdout.decode(), p.stderr.decode()
                )
            )
        p.check_returncode()
