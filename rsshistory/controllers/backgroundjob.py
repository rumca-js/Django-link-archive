from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    LinkDataModel,
    BackgroundJob,
    PersistentInfo,
)
from ..webtools import HtmlPage


class BackgroundJobController(BackgroundJob):
    class Meta:
        proxy = True

    def truncate():
        BackgroundJob.objects.all().delete()

    def truncate_invalid_jobs():
        job_choices = BackgroundJob.JOB_CHOICES
        valid_jobs_choices = []
        for job_choice in job_choices:
            valid_jobs_choices.append(job_choice[0])

        jobs = BackgroundJob.objects.all()
        for job in jobs:
            if job.job not in valid_jobs_choices:
                print("Clearing job {}".format(job.job))
                job.delete()

    def get_number_of_jobs(job_name=None):
        if job_name is None:
            return BackgroundJob.objects.all().count()
        return BackgroundJob.objects.filter(job=job_name).count()

    def create_single_job(job_name, subject="", args=""):
        try:
            items = BackgroundJob.objects.filter(job=job_name, subject=subject)
            if items.count() == 0:
                return BackgroundJob.objects.create(
                    job=job_name,
                    task=None,
                    subject=subject,
                    args=args,
                )
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: {}: {} {}".format(job_name, str(e), error_text)
            )

    def download_rss(source, force=False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PROCESS_SOURCE, source.url
        )

    def download_music(item):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, item.link
        )

    def download_video(item):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, item.link
        )

    def update_entry_data(url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_UPDATE_DATA, url
        )

    def link_add(url, source = None):
        h = HtmlPage(url)
        if h.is_analytics():
            return

        existing = LinkDataModel.objects.filter(link=url)
        if existing.count() > 0:
            return

        if source:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_ADD, url, str(source.id),
            )
        else:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_ADD, url,
            )

    def link_scan(url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_SCAN, url,
        )

    def write_daily_data_range(date_start=date.today(), date_stop=date.today()):
        try:
            if date_stop < date_start:
                PersistentInfo.error(
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
            PersistentInfo.error(
                "Exception: Daily data: {} {}".format(str(e), error_text)
            )

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
            PersistentInfo.error(
                "Exception: Daily data: {} {}".format(str(e), error_text)
            )

    def write_tag_data(tag):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_TOPIC_DATA, tag
        )

    def write_bookmarks():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_BOOKMARKS
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

    def link_save(link_url):
        try:
            archive_items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_LINK_SAVE
            )
            if archive_items.count() < 100:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_LINK_SAVE,
                    task=None,
                    subject=link_url,
                    args="",
                )
                return True
            else:
                for key, obj in enumerate(archive_items):
                    if key > 100:
                        obj.delete()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Link archive: {} {}".format(str(e), error_text)
            )

    def link_download(link_url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD, link_url
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

    def import_from_instance(link):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_INSTANCE, link
        )