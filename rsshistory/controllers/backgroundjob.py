from datetime import datetime, date, timedelta
import os
import json
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    LinkDataModel,
    SourceDataModel,
    BackgroundJob,
    AppLogging,
    ModelFiles,
)
from ..webtools import HtmlPage, DomainAwarePage, Url
from ..dateutils import DateUtils


class BackgroundJobController(BackgroundJob):
    # fmt: off
    PRIORITY_JOB_CHOICES = [
        (BackgroundJob.JOB_EXPORT_DATA, BackgroundJob.JOB_EXPORT_DATA), # 0

        (BackgroundJob.JOB_WRITE_DAILY_DATA, BackgroundJob.JOB_WRITE_DAILY_DATA), # 1
        (BackgroundJob.JOB_WRITE_TOPIC_DATA, BackgroundJob.JOB_WRITE_TOPIC_DATA), # 2
        (BackgroundJob.JOB_WRITE_YEAR_DATA, BackgroundJob.JOB_WRITE_YEAR_DATA), # 3
        (BackgroundJob.JOB_WRITE_NOTIME_DATA, BackgroundJob.JOB_WRITE_NOTIME_DATA), # 4

        (BackgroundJob.JOB_IMPORT_DAILY_DATA, BackgroundJob.JOB_IMPORT_DAILY_DATA), # 5
        (BackgroundJob.JOB_IMPORT_BOOKMARKS, BackgroundJob.JOB_IMPORT_BOOKMARKS), # 6
        (BackgroundJob.JOB_IMPORT_SOURCES, BackgroundJob.JOB_IMPORT_SOURCES), # 7
        (BackgroundJob.JOB_IMPORT_INSTANCE, BackgroundJob.JOB_IMPORT_INSTANCE), # 8
        (BackgroundJob.JOB_IMPORT_FROM_FILES, BackgroundJob.JOB_IMPORT_FROM_FILES), # 9

        # Since cleanup, moving to archives can take forever, we still want to process
        # source in between
        (BackgroundJob.JOB_PROCESS_SOURCE, BackgroundJob.JOB_PROCESS_SOURCE,), # 10
        (BackgroundJob.JOB_CLEANUP, BackgroundJob.JOB_CLEANUP), # 11
        (BackgroundJob.JOB_MOVE_TO_ARCHIVE, BackgroundJob.JOB_MOVE_TO_ARCHIVE), # 12
        (BackgroundJob.JOB_LINK_ADD, BackgroundJob.JOB_LINK_ADD,), # 13                         # adds link using default properties, may contain link map properties in the map
        (BackgroundJob.JOB_LINK_UPDATE_DATA, BackgroundJob.JOB_LINK_UPDATE_DATA),           # update data, recalculate
        (BackgroundJob.JOB_LINK_RESET_LOCAL_DATA, BackgroundJob.JOB_LINK_RESET_LOCAL_DATA),           # update data, recalculate
        (BackgroundJob.JOB_LINK_RESET_DATA, BackgroundJob.JOB_LINK_RESET_DATA,),
        (BackgroundJob.JOB_LINK_SAVE, BackgroundJob.JOB_LINK_SAVE,),                        # link is saved using thirdparty pages (archive.org)
        (BackgroundJob.JOB_LINK_SCAN, BackgroundJob.JOB_LINK_SCAN,),
        (BackgroundJob.JOB_LINK_DOWNLOAD, BackgroundJob.JOB_LINK_DOWNLOAD),                 # link is downloaded using wget
        (BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC),     #
        (BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO),     #
        (BackgroundJob.JOB_DOWNLOAD_FILE, BackgroundJob.JOB_DOWNLOAD_FILE,),
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

    def get_link(self):
        if self.job == BackgroundJob.JOB_PROCESS_SOURCE:
            source = self.get_text_to_source(self.subject)
            if source:
                return source.get_absolute_url()
        elif self.job == BackgroundJob.JOB_LINK_UPDATE_DATA:
            entry = self.get_text_to_entry(self.subject)
            if entry:
                return entry.get_absolute_url()
        elif self.job == BackgroundJob.JOB_LINK_RESET_DATA:
            entry = self.get_text_to_entry(self.subject)
            if entry:
                return entry.get_absolute_url()
        elif self.job == BackgroundJob.JOB_LINK_RESET_LOCAL_DATA:
            entry = self.get_text_to_entry(self.subject)
            if entry:
                return entry.get_absolute_url()

        if self.args and self.args != "":
            p = DomainAwarePage(self.args)
            if p.is_web_link():
                return self.args

            try:
                cfg = json.loads(self.args)

                if "entry_id" in cfg:
                    entry = self.get_text_to_entry(cfg["entry_id"])
                    if entry:
                        return entry.get_absolute_url()
                elif "source_id" in cfg:
                    source = self.get_text_to_source(cfg["source_id"])
                    if source:
                        return source.get_absolute_url()
            except Exception as E:
                AppLogging.debug(E, "Error when loading JSON: {}".format(self.args))
                return

    def is_subject_link(self):
        p = DomainAwarePage(self.subject)
        if p.is_web_link():
            return True

    def get_text_to_source(self, text):
        try:
            source_id = int(text)
        except Exception as e:
            return

        sources = SourceDataModel.objects.filter(id=source_id)
        if sources.exists():
            return sources[0]

    def get_text_to_entry(self, text):
        try:
            entry_id = int(text)
        except Exception as e:
            return

        entries = LinkDataModel.objects.filter(id=entry_id)
        if entries.exists():
            return entries[0]

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

        # anything not in priority list goes at the end
        return len(BackgroundJobController.JOB_CHOICES) + 1

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
        except Exception as E:
            AppLogging.exc(
                    E, "Creating single job_name:{}, subject:{}, args:{}".format(job_name, subject, args)
            )

    def download_rss(source, force=False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PROCESS_SOURCE, source.id, source.title
        )

    def download_music(entry):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, entry.link
        )

    def download_video(entry):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, entry.link
        )

    def download_music_url(url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, url
        )

    def download_video_url(entry):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, url
        )

    def link_add(url, source=None, tag="", user=None, properties=None):
        from ..configuration import Configuration
        from .entriesutils import EntryWrapper

        """
        It handles only automatic additions.
        """
        input_url = url

        url = Url.get_cleaned_link(url)  # TODO maybe urlhandler?

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
            if not config.accept_not_domain_entries and config.accept_domains:
                url = h.get_domain()
        else:
            """TODO This should be configurable"""
            return

        w = EntryWrapper(url)

        entry = w.get()
        if entry:
            if properties is not None:
                if "permanent" in properties:
                    entry.permanent = properties["permanent"]
                if "bookmarked" in properties:
                    entry.bookmarked = properties["bookmarked"]
            entry.save()
            return

        cfg = {}

        if source:
            cfg["source_id"] = source.id

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

        p = DomainAwarePage(url)
        if not p.is_web_link():

            stack_lines = traceback.format_stack()
            error_lines = "".join(stack_lines)

            AppLogging.error("Someone tries to add invalid link:{} input_url:{} lines:\n{}".format(url, input_url, error_lines))
            return

        if cfg != {}:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_ADD, url, args_text
            )
        else:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_LINK_ADD,
                url,
            )

    def link_scan(url=None, entry=None, source=None):
        cfg = {}

        if source:
            cfg["source_id"] = source.id

        if entry:
            cfg["entry_id"] = entry.id

        if entry:
            url = entry.link

        if url is None:
            AppLogging.error("URL is NULL")
            return

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

    def download_file(url=None):
        if url is None:
            return

        if not ModelFiles.objects.filter(file_name = url).exists():
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_DOWNLOAD_FILE,
                url,)

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
        except Exception as E:
            AppLogging.exc(E, "write_daily_data_range: {} {}".format(date_start, date_stop))

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
            AppLogging.exc(E, "write_daily_data_str: {} {}".format(date_start, date_stop))

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
        except Exception as E:
            AppLogging.exc(
                    "link_save. Link URL:{}".format(link_url)
            )

    def link_download(link_url):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD, link_url
        )

    def entry_update_data(entry, force=False):
        """
        Do not update, if it was updated recently, or if we are missing key components
        """
        if not force:
            if not entry.is_update_time():
                return

        if BackgroundJobController.is_update_or_reset_entry_job(entry):
            return

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_UPDATE_DATA,
            entry.id,
            entry.link,
        )

    def entry_reset_local_data(entry):
        """ """
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_RESET_LOCAL_DATA,
            entry.id,
            entry.link,
        )

    def entry_reset_data(entry, force=False):
        """
        Do not update, if it was updated recently
        """
        if not force:
            if not entry.is_reset_time():
                return

        if BackgroundJobController.is_update_or_reset_entry_job(entry):
            return

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_RESET_DATA, entry.id, entry.link
        )

    def export_data(export, input_date=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_EXPORT_DATA, str(export.id), input_date
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

    def get_number_of_update_reset_jobs():
        condition_reset = Q(job=BackgroundJob.JOB_LINK_RESET_DATA)
        condition_update = Q(job=BackgroundJob.JOB_LINK_UPDATE_DATA)
        condition_enabled = Q(enabled=True)

        objs = BackgroundJobController.objects.filter(
            condition_enabled & (condition_update | condition_reset)
        )
        return objs.count()

    def is_update_or_reset_entry_job(entry):
        condition_reset = Q(job=BackgroundJob.JOB_LINK_RESET_DATA)
        condition_update = Q(job=BackgroundJob.JOB_LINK_UPDATE_DATA)
        condition_enabled = Q(enabled=True)
        condition_subject = Q(subject=str(entry.id))

        objs = BackgroundJobController.objects.filter(
            condition_subject & condition_enabled & (condition_update | condition_reset)
        )
        return objs.count() > 0
