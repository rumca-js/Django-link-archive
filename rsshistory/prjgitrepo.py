import shutil

from .gitrepo import GitRepo
from .dateutils import DateUtils


class DailyRepo(GitRepo):

    def __init__(self, git_data, git_repo):
        super().__init__(git_data, git_repo)

    def is_day_data_present(self, day):
       expected_dir = self.get_local_day_path(day)

       if expected_dir.is_dir():
           return True

       return False

    def get_local_day_path(self, day):
        return self.get_local_dir() / DateUtils.get_datetime_year(day) / DateUtils.get_datetime_month(day) / DateUtils.get_dir4date(day)

    def copy_day_data(self, daily_data_path, day):
        full_local = self.get_local_day_path(day)

        if not full_local.exists():
            full_local.mkdir()

        shutil.copytree(daily_data_path, full_local, dirs_exist_ok = True)

    def copy_file(self, file_name):
        local_dir = self.get_local_dir()
        shutil.copy(file_name, local_dir)


class MainRepo(GitRepo):

    def __init__(self, git_data, git_repo):
        super().__init__(git_data, git_repo)

    def copy_main_data(self, main_path):
       local_dir = main_path
       expected_dir = self.get_local_dir()

       shutil.copytree(local_dir, expected_dir, dirs_exist_ok = True)
