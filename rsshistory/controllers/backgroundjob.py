from datetime import datetime, date, timedelta
import os
import traceback
import json

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    LinkDataModel,
    BackgroundJob,
    AppLogging,
)
from ..webtools import HtmlPage, DomainAwarePage, Url
from ..dateutils import DateUtils


class BackgroundJobController(BackgroundJob):
    # fmt: off
    PRIORITY_JOB_CHOICES = [
        (BackgroundJob.JOB_PUSH_TO_REPO, BackgroundJob.JOB_PUSH_TO_REPO), # 0
        (BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO, BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO), # 1
        (BackgroundJob.JOB_PUSH_YEAR_DATA_TO_REPO, BackgroundJob.JOB_PUSH_YEAR_DATA_TO_REPO), # 2
        (BackgroundJob.JOB_PUSH_NOTIME_DATA_TO_REPO, BackgroundJob.JOB_PUSH_NOTIME_DATA_TO_REPO), # 3

        (BackgroundJob.JOB_WRITE_DAILY_DATA, BackgroundJob.JOB_WRITE_DAILY_DATA), # 4
        (BackgroundJob.JOB_WRITE_TOPIC_DATA, BackgroundJob.JOB_WRITE_TOPIC_DATA), # 5
        (BackgroundJob.JOB_WRITE_YEAR_DATA, BackgroundJob.JOB_WRITE_YEAR_DATA), # 6
        (BackgroundJob.JOB_WRITE_NOTIME_DATA, BackgroundJob.JOB_WRITE_NOTIME_DATA), # 6

        (BackgroundJob.JOB_IMPORT_DAILY_DATA, BackgroundJob.JOB_IMPORT_DAILY_DATA), # 7
        (BackgroundJob.JOB_IMPORT_BOOKMARKS, BackgroundJob.JOB_IMPORT_BOOKMARKS), # 8
        (BackgroundJob.JOB_IMPORT_SOURCES, BackgroundJob.JOB_IMPORT_SOURCES), # 9
        (BackgroundJob.JOB_IMPORT_INSTANCE, BackgroundJob.JOB_IMPORT_INSTANCE), # 10
        (BackgroundJob.JOB_IMPORT_FROM_FILES, BackgroundJob.JOB_IMPORT_FROM_FILES), # 11

        # Since cleanup, moving to archives can take forever, we still want to process
        # source in between
        (BackgroundJob.JOB_PROCESS_SOURCE, BackgroundJob.JOB_PROCESS_SOURCE,), # 12
        (BackgroundJob.JOB_CLEANUP, BackgroundJob.JOB_CLEANUP), # 13
        (BackgroundJob.JOB_MOVE_TO_ARCHIVE, BackgroundJob.JOB_MOVE_TO_ARCHIVE), # 14
        (BackgroundJob.JOB_LINK_ADD, BackgroundJob.JOB_LINK_ADD,), # 15                         # adds link using default properties, may contain link map properties in the map
        (BackgroundJob.JOB_LINK_UPDATE_DATA, BackgroundJob.JOB_LINK_UPDATE_DATA),           # update data, recalculate
        (BackgroundJob.JOB_LINK_RESET_DATA, BackgroundJob.JOB_LINK_RESET_DATA,),
        (BackgroundJob.JOB_LINK_SAVE, BackgroundJob.JOB_LINK_SAVE,),                        # link is saved using thirdparty pages (archive.org)
        (BackgroundJob.JOB_LINK_SCAN, BackgroundJob.JOB_LINK_SCAN,),
        (BackgroundJob.JOB_LINK_DOWNLOAD, BackgroundJob.JOB_LINK_DOWNLOAD),                 # link is downloaded using wget
        (BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC),     #
        (BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO),     #
        (BackgroundJob.JOB_CHECK_DOMAINS, BackgroundJob.JOB_CHECK_DOMAINS),
    ]
    # fmt: on

    class Meta:
        proxy = True

    def truncate():
        BackgroundJob.objects.all().delete()

    def on_error(self):
        self.errors += 1

        if self.errors > 5:
            self.enabled = False

            AppLogging.error(
                "Disabling job due to errors {} {} {}".format(
                    self.job, self.subject, self.args
                )
            )

        # TODO Add notification

        self.save()

    def enable(self):
        self.errors = 0
        self.enabled = True
        self.priority = BackgroundJobController.get_job_priority(self.job)

        self.save()

    def disable(self):
        self.enabled = False
        self.save()

    def truncate_invalid_jobs():
        job_choices = BackgroundJobController.JOB_CHOICES
        valid_jobs_choices = []
        for job_choice in job_choices:
            valid_jobs_choices.append(job_choice[0])

        jobs = BackgroundJob.objects.all()
        for job in jobs:
            if job.job not in valid_jobs_choices:
                job.delete()

    def get_number_of_jobs(job_name=None):
        if job_name is None:
            return BackgroundJob.objects.all().count()
        return BackgroundJob.objects.filter(job=job_name).count()

    def get_job_priority(job_name):
        index = 0
        job_choices = BackgroundJobController.PRIORITY_JOB_CHOICES
        for job_choice in job_choices:
            if job_choice[0] == job_name:
                return index
            index += 1

        return 100

    def create_single_job(job_name, subject="", args=""):
        try:
            items = BackgroundJob.objects.filter(job=job_name, subject=subject)
            if items.count() == 0:
                return BackgroundJob.objects.create(
                    job=job_name,
                    task=None,
                    subject=subject,
                    args=args,
                    priority=BackgroundJobController.get_job_priority(job_name),
                )
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception: {}: {} {}".format(job_name, str(e), error_text)
            )

    def download_rss(source, force=False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PROCESS_SOURCE, source.url, source.title
        )

    def download_music(item):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, item.link
        )

    def download_video(item):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, item.link
        )

    def link_add(url, source=None, tag="", user=None, properties=None):
        from ..configuration import Configuration

        """
        It handles only automatic additions.
        """
        url = Url.get_cleaned_link(url) # TODO maybe urlhandler?

        h = DomainAwarePage(url)
        if h.is_analytics():
            return

        """
        TODO: there should be some one place to verify if link is 'accepted' to be added
        If it is not link service we may only accept domains.
        If it is link service - add as is.
        In link add thread we will 'unpack links service'.
        """
        if not h.is_link_service():
            config = Configuration.get_object().config_entry
            if not config.auto_store_entries and config.auto_store_domain_info:
                url = h.get_domain()
        else:
            """TODO This should be configurable"""
            return

        existing = LinkDataModel.objects.filter(link=url)
        if existing.count() > 0:
            return

        cfg = {}

        if source:
            cfg["source"] = source.id

        if tag:
            cfg["tag"] = tag

        if user:
            cfg["user_id"] = user.id

        if properties:
            cfg["properties"] = properties

        args_text = json.dumps(cfg)

        """TODO fix hardcoded value"""
        if len(args_text) > 1000:
            AppLogging.error(
                "Link add job configuration is too long:{}".format(args_text)
            )
            args_text = ""

        if cfg != {}:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_ADD, url, args_text
            )
        else:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_ADD,
                url,
            )

    def link_scan(url, source=None):

        cfg = {}

        if source:
            cfg["source"] = source.id

        args_text = json.dumps(cfg)

        """TODO fix hardcoded value"""
        if len(args_text) > 1000:
            AppLogging.error(
                "Link add job configuration is too long:{}".format(args_text)
            )
            args_text = ""

        if cfg != {}:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_SCAN,
                url,
                args_text,
            )
        else:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_SCAN,
                url,
            )

    def write_daily_data_range(date_start=date.today(), date_stop=date.today()):
        try:
            if date_stop < date_start:
                AppLogging.error(
                    "Yearly generation: Incorrect configuration of dates start:{} stop:{}".format(
                        date_start, date_stop
                    )
                )
                return False

            sent = False
            current_date = date_start
            while current_date <= date_stop:
                str_date = current_date.isoformat()
                current_date += timedelta(days=1)

                BackgroundJobController.write_daily_data(str_date)
                sent = True

            return sent
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: Daily data: {} {}".format(str(e), error_text))

    def write_daily_data(input_date):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_DAILY_DATA, input_date
        )

    def write_daily_data_str(start="2022-01-01", stop="2022-12-31"):
        try:
            date_start = datetime.strptime(start, "%Y-%m-%d").date()
            date_stop = datetime.strptime(stop, "%Y-%m-%d").date()

            BackgroundJobController.write_daily_data_range(date_start, date_stop)
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error("Exception: Daily data: {} {}".format(str(e), error_text))

    def write_tag_data(tag):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_TOPIC_DATA, tag
        )

    def import_daily_data():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_DAILY_DATA
        )

    def import_bookmarks():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_BOOKMARKS
        )

    def import_sources():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_SOURCES
        )

    def import_from_files(data=None):
        if not data:
            return

        args_text = json.dumps(data)

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_FROM_FILES, args_text
        )

    def link_save(link_url):
        try:
            archive_items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_LINK_SAVE
            )
            if archive_items.count() < 100:
                return BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_LINK_SAVE,
                    task=None,
                    subject=link_url,
                    args="",
                    priority=BackgroundJobController.get_job_priority(
                        BackgroundJob.JOB_LINK_SAVE
                    ),
                )
            else:
                for key, obj in enumerate(archive_items):
                    if key > 100:
                        obj.delete()
        except Exception as e:
            error_text = traceback.format_exc()
            AppLogging.error(
                "Exception: Link archive: {} {}".format(str(e), error_text)
            )

    def link_download(link_url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD, link_url
        )

    def entry_update_data(entry, force=False):
        """
        Do not update, if it was updated recently, or if we are missing key components
        """
        if entry.is_dead():
            return

        if not force:
            if (
                entry.page_rating > 0
                and entry.page_rating_contents > 0
                and entry.date_update_last
                > DateUtils.get_datetime_now_utc() - timedelta(days=30)
            ):
                return

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_UPDATE_DATA, entry.link
        )

    def entry_reset_data(entry, force=False):
        """
        Do not update, if it was updated recently
        """
        if entry.is_dead():
            return

        if not force:
            if entry.date_update_last > DateUtils.get_datetime_now_utc() - timedelta(
                days=1
            ):
                return

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_RESET_DATA, entry.link
        )

    def push_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_TO_REPO, input_date
        )

    def push_daily_data_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_DAILY_DATA_TO_REPO, input_date
        )

    def push_year_data_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_YEAR_DATA_TO_REPO, input_date
        )

    def push_notime_data_to_repo(input_date=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PUSH_NOTIME_DATA_TO_REPO, input_date
        )

    def make_cleanup():
        return BackgroundJobController.create_single_job(BackgroundJob.JOB_CLEANUP)

    def check_domains():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CHECK_DOMAINS
        )

    def import_from_instance(link, author=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_INSTANCE, link, author
        )
