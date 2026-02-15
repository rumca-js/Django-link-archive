from datetime import datetime, date, timedelta
import os
import json
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q
from django.conf import settings

from webtoolkit import UrlLocation
from utils.dateutils import DateUtils

from ..models import (
    LinkDataModel,
    SourceDataModel,
    BackgroundJob,
    AppLogging,
    ModelFiles,
    EntryRules,
)
from ..apps import LinkDatabase


class BackgroundJobController(BackgroundJob):
    # fmt: off
    PRIORITY_JOB_CHOICES = [
        (BackgroundJob.JOB_INITIALIZE, BackgroundJob.JOB_INITIALIZE),
        (BackgroundJob.JOB_INITIALIZE_BLOCK_LIST, BackgroundJob.JOB_INITIALIZE_BLOCK_LIST),

        (BackgroundJob.JOB_EXPORT_DATA, BackgroundJob.JOB_EXPORT_DATA),

        (BackgroundJob.JOB_WRITE_DAILY_DATA, BackgroundJob.JOB_WRITE_DAILY_DATA),
        (BackgroundJob.JOB_WRITE_TOPIC_DATA, BackgroundJob.JOB_WRITE_TOPIC_DATA),
        (BackgroundJob.JOB_WRITE_YEAR_DATA, BackgroundJob.JOB_WRITE_YEAR_DATA),
        (BackgroundJob.JOB_WRITE_NOTIME_DATA, BackgroundJob.JOB_WRITE_NOTIME_DATA),

        (BackgroundJob.JOB_IMPORT_DAILY_DATA, BackgroundJob.JOB_IMPORT_DAILY_DATA),
        (BackgroundJob.JOB_IMPORT_BOOKMARKS, BackgroundJob.JOB_IMPORT_BOOKMARKS),
        (BackgroundJob.JOB_IMPORT_SOURCES, BackgroundJob.JOB_IMPORT_SOURCES),
        (BackgroundJob.JOB_IMPORT_INSTANCE, BackgroundJob.JOB_IMPORT_INSTANCE),
        (BackgroundJob.JOB_IMPORT_FROM_FILES, BackgroundJob.JOB_IMPORT_FROM_FILES),

        # Since cleanup, moving to archives can take forever, we still want to process
        # source in between
        (BackgroundJob.JOB_PROCESS_SOURCE, BackgroundJob.JOB_PROCESS_SOURCE,),
        (BackgroundJob.JOB_CLEANUP, BackgroundJob.JOB_CLEANUP),
        (BackgroundJob.JOB_TRUNCATE_TABLE, BackgroundJob.JOB_TRUNCATE_TABLE),
        (BackgroundJob.JOB_MOVE_TO_ARCHIVE, BackgroundJob.JOB_MOVE_TO_ARCHIVE),
        (BackgroundJob.JOB_LINK_RESET_LOCAL_DATA, BackgroundJob.JOB_LINK_RESET_LOCAL_DATA),           # update data, recalculate
        (BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL, BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL),
        (BackgroundJob.JOB_LINK_UPDATE_DATA, BackgroundJob.JOB_LINK_UPDATE_DATA),
        (BackgroundJob.JOB_LINK_RESET_DATA, BackgroundJob.JOB_LINK_RESET_DATA,),
        (BackgroundJob.JOB_LINK_ADD, BackgroundJob.JOB_LINK_ADD,),
        (BackgroundJob.JOB_LINK_SAVE, BackgroundJob.JOB_LINK_SAVE,),
        (BackgroundJob.JOB_LINK_SCAN, BackgroundJob.JOB_LINK_SCAN,),
        (BackgroundJob.JOB_SOURCE_ADD, BackgroundJob.JOB_SOURCE_ADD,),
        (BackgroundJob.JOB_LINK_DOWNLOAD, BackgroundJob.JOB_LINK_DOWNLOAD),
        (BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC, BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC),
        (BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO, BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO),
        (BackgroundJob.JOB_DOWNLOAD_FILE, BackgroundJob.JOB_DOWNLOAD_FILE,),
        (BackgroundJob.JOB_CHECK_DOMAINS, BackgroundJob.JOB_CHECK_DOMAINS),
        (BackgroundJob.JOB_RUN_RULE, BackgroundJob.JOB_RUN_RULE),
    ]
    # fmt: on

    class Meta:
        proxy = True

    def enable(self):
        self.errors = 0
        self.enabled = True
        self.priority = BackgroundJobController.get_job_priority(self.job)

        self.save()

    def disable(self):
        self.enabled = False
        self.save()

    def get_number_of_jobs(job_name=None, only_enabled=True):
        condition = Q()
        if job_name is not None:
            condition = condition & Q(job=job_name)

        if only_enabled:
            condition = condition & Q(enabled=True)

        return BackgroundJob.objects.filter(condition).count()

    def get_job_priority(job_name):
        index = 0
        job_choices = BackgroundJobController.PRIORITY_JOB_CHOICES
        for job_choice in job_choices:
            if job_choice[0] == job_name:
                return index
            index += 1

        # anything not in priority list goes at the end
        return len(BackgroundJobController.JOB_CHOICES) + 1

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
        return objs.exists()

    def create_single_job(job_name, subject="", args="", user=None, cfg=None):
        from ..configuration import Configuration

        args_text = args
        if args_text == "" and cfg:
            args_text = json.dumps(cfg)

        items = BackgroundJobController.objects.filter(job=job_name, subject=subject)
        if not items.exists():
            job = BackgroundJobController.objects.create(
                job=job_name,
                task=None,
                subject=subject,
                args=args_text,
                priority=BackgroundJobController.get_job_priority(job_name),
                user=user,
            )

            config = Configuration.get_object().config_entry
            if job and not config.enable_background_jobs:
                BackgroundJobController.run_single_job(job)

            else:
                return job

    def run_single_job(job):
        from ..threadprocessors import GenericJobsProcessor

        processor = GenericJobsProcessor()
        processor.run_one_job(job)

    def truncate_invalid_jobs():
        job_choices = BackgroundJobController.JOB_CHOICES
        valid_jobs_choices = []
        for job_choice in job_choices:
            valid_jobs_choices.append(job_choice[0])

        jobs = BackgroundJob.objects.all()
        for job in jobs:
            if job.job not in valid_jobs_choices:
                job.delete()

    # job functions are defined below

    def download_rss(source, force=False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_PROCESS_SOURCE, subject=source.id, args=source.title
        )

    def download_music(entry, user=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC,
            subject=entry.link,
            user=user,
        )

    def download_video(entry, user=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO,
            subject=entry.link,
            user=user,
        )

    def download_music_url(url, user=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC,
            subject=url,
            user=user,
        )

    def download_video_url(url, user=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO,
            subject=url,
            user=user,
        )

    def link_add(url, source=None, tag="", user=None, properties=None, browser=None):
        from ..configuration import Configuration
        from .entrywrapper import EntryWrapper

        """
        It handles only automatic additions.
        """
        url = UrlLocation.get_cleaned_link(url)

        if not url:
            return

        if EntryRules.is_url_blocked(url):
            return

        h = UrlLocation(url)
        if h.is_analytics():
            return

        if not h.is_web_link():
            return

        """
        TODO: there should be some one place to verify if link is 'accepted' to be added
        If it is not link service we may only accept domains.
        If it is link service - add as is.
        In link add thread we will 'unpack links service'.
        """
        if not h.is_link_service():
            config = Configuration.get_object().config_entry
            if not config.accept_non_domain_links and config.accept_domain_links:
                url = h.get_domain()
        else:
            """TODO This should be configurable"""
            return

        w = EntryWrapper(url)

        entry = w.get()
        if entry:
            if properties is not None:
                new_bookmarked = properties.get("bookmarked")
                if new_bookmarked is not None:
                    entry.bookmarked = new_bookmarked
                # Do not set permanent. it is calculated
            entry.save()
            return

        cfg = {}

        if source:
            cfg["source_id"] = source.id

        if browser:
            cfg["browser"] = browser.id

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

    def get_cfg(self):
        cfg = {}
        if self.args != "":
            try:
                cfg = json.loads(self.args)
            except ValueError as E:
                pass
            except TypeError as E:
                pass
        return cfg

    def source_add(url, properties=None):
        cfg = {}
        cfg["url"] = url

        if properties:
            cfg["properties"] = properties

        if cfg != {}:
            args_text = json.dumps(cfg)

            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_SOURCE_ADD, url, args_text
            )
        else:
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_SOURCE_ADD,
                url,
            )

    def link_scan(url=None, entry=None, source=None, browser=None):
        from ..configuration import Configuration

        cfg = {}

        config = Configuration.get_object().config_entry

        if not config.auto_scan_new_entries:
            return

        if source:
            cfg["source_id"] = source.id

        if entry:
            cfg["entry_id"] = entry.id

        if browser:
            cfg["browser"] = browser.id

        if entry:
            url = entry.link

        if url is None:
            AppLogging.error("URL is NULL")
            return

        if EntryRules.is_url_blocked(url):
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

    def source_link_add(source):
        if not source.enabled:
            return

        properties = {"permament": True}
        return BackgroundJobController.link_add(
            url=source.url, properties=properties, source=source
        )

    def download_file(url=None, user=None):
        if url is None:
            return

        if not ModelFiles.objects.filter(file_name=url).exists():
            return BackgroundJobController.create_single_job(
                BackgroundJob.JOB_DOWNLOAD_FILE,
                subject=url,
                user=user,
            )

    def write_daily_data_range(date_start=date.today(), date_stop=date.today()):
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

    def write_daily_data(input_date):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_WRITE_DAILY_DATA, input_date
        )

    def write_daily_data_str(start="2022-01-01", stop="2022-12-31"):
        date_start = datetime.strptime(start, "%Y-%m-%d").date()
        date_stop = datetime.strptime(stop, "%Y-%m-%d").date()

        BackgroundJobController.write_daily_data_range(date_start, date_stop)

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
            job_name=BackgroundJob.JOB_IMPORT_FROM_FILES, args=args_text
        )

    def link_save(link_url):
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry
        if not config.enable_link_archiving:
            return

        return BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_SAVE,
            task=None,
            subject=link_url,
            args="",
            priority=BackgroundJobController.get_job_priority(
                BackgroundJob.JOB_LINK_SAVE
            ),
        )

    def link_download_social_data(entry):
        from ..configuration import Configuration

        return BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL,
            task=None,
            subject=entry.id,
            args="",
            priority=BackgroundJobController.get_job_priority(
                BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL
            ),
        )

    def link_download(link_url, user=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_DOWNLOAD,
            subject=link_url,
            user=user,
        )

    def entry_update_data(entry, browser=None, force=False):
        """
        Do not update, if it was updated recently, or if we are missing key components
        """
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry
        if not config.entry_update_via_internet:
            return

        if not force:
            if not entry.is_update_time():
                return

        if BackgroundJobController.is_update_or_reset_entry_job(entry):
            return

        args = {}
        args["id"] = entry.id
        args["link"] = entry.link

        if browser:
            args["browser"] = browser.id

        args_text = json.dumps(args)

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_UPDATE_DATA,
            entry.id,
            args_text,
        )

    def entry_reset_local_data(entry):
        """ """
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_RESET_LOCAL_DATA,
            entry.id,
            entry.link,
        )

    def entry_reset_data(entry, force=False, browser=None):
        """
        Do not update, if it was updated recently
        """
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry
        if not config.entry_update_via_internet:
            return

        if not force:
            if not entry.is_reset_time():
                return

        if BackgroundJobController.is_update_or_reset_entry_job(entry):
            return

        args = {}
        args["id"] = entry.id
        args["link"] = entry.link

        if browser:
            args["browser"] = browser.id
        args_text = json.dumps(args)

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_LINK_RESET_DATA, entry.id, args_text
        )

    def export_data(export, input_date=None, user=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_EXPORT_DATA,
            subject=str(export.id),
            args=input_date,
            user=user,
        )

    def make_cleanup(table="", cfg=None, verify=False):
        pass_cfg = {}

        if cfg:
            pass_cfg = cfg

        if verify:
            pass_cfg["verify"] = True

        args_text = ""
        try:
            args_text = json.dumps(pass_cfg)
        except ValueError as E:
            pass

        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CLEANUP, subject=table, args=args_text
        )

    def check_domains():
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_CHECK_DOMAINS
        )

    def import_from_instance(link, author=""):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_IMPORT_INSTANCE,
            subject=link,
            args=author,
        )

    def run_rule(rule, user=None):
        return BackgroundJobController.create_single_job(
            BackgroundJob.JOB_RUN_RULE,
            subject=str(rule.id),
            user=user,
        )

    def truncate():
        BackgroundJob.objects.all().delete()

    def on_error(self):
        """
        Disabling background jobs at the second attempt.
        """
        self.errors += 1

        if self.errors > 1:
            self.enabled = False

            AppLogging.error(
                "Job:{}. Disabling job due to errors {} {}".format(
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
        elif self.job == BackgroundJob.JOB_EXPORT_DATA:
            id = self.subject
            if id and id != "":
                return reverse("{}:data-export".format(LinkDatabase.name), args=[id])

        if self.args and self.args != "":
            p = UrlLocation(self.args)
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
            except ValueError as E:
                AppLogging.debug(E, "Error when loading JSON: {}".format(self.args))
                return

    def get_source(self):
        source = self.get_text_to_source(self.subject)
        return source

    def is_subject_link(self):
        p = UrlLocation(self.subject)
        if p.is_web_link():
            return True

    def get_text_to_source(self, text):
        try:
            source_id = int(text)
        except ValueError:
            return

        sources = SourceDataModel.objects.filter(id=source_id)
        if sources.exists():
            return sources[0]

    def get_text_to_entry(self, text):
        try:
            entry_id = int(text)
        except ValueError as E:
            return

        entries = LinkDataModel.objects.filter(id=entry_id)
        if entries.exists():
            return entries[0]

    def cleanup(cfg):
        jobs = BackgroundJobController.objects.all()
        for job in jobs:
            is_valid = BackgroundJobController.is_job_valid(job)

            if not is_valid:
                AppLogging.error(f"Removing job:{job}. The job, or processors are incorrectly configured")
                job.delete()

    def is_job_valid(job):
        from ..threadprocessors import processor_from_id

        processors_infos = settings.PROCESSORS_INFO

        picked_up = False
        for processors_info in processors_infos:
            processor = processor_from_id(processors_info[1])
            if processor:
                processor_obj = processor(processors_list=processors_infos)
                conditions = processor_obj.get_query_conditions()

                filtered = BackgroundJobController.objects.filter(Q(id=job.id) & conditions)
                if filtered.exists():
                    picked_up = True

        return picked_up

    def truncate(cfg):
        if "enabled" in cfg:
            jobs = BackgroundJobController.objects.filter(*cfg)
            jobs.delete()
