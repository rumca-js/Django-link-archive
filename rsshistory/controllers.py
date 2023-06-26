from datetime import datetime, date, timedelta

from django.db.models import Q

from .models import LinkCommentDataModel, BackgroundJob


class LinkCommentDataController(object):
    def __init__(self, comment):
        pass

    def can_user_add_comment(user_name):
        now = datetime.now()
        time_start = now - timedelta(days=1)
        time_stop = now

        criterion0 = Q(author=user_name)
        criterion1 = Q(date_published__range=[time_start, time_stop])
        criterion2 = Q(date_edited__range=[time_start, time_stop])

        comments = LinkCommentDataModel.objects.filter(
            criterion0 & (criterion1 | criterion2)
        )
        if len(comments) > 0:
            return False

        return True


class BackgroundJobController(object):
    def __init__(self):
        pass

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

    def get_number_of_jobs(job_type):
        return len(BackgroundJob.objects.filter(job=job_type))

    def download_rss(source, force=False):
        if force == False:
            if source.is_fetch_possible() == False:
                return False

        if (
            len(
                BackgroundJob.objects.filter(
                    job=BackgroundJob.JOB_PROCESS_SOURCE, subject=source.url
                )
            )
            == 0
        ):
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_PROCESS_SOURCE,
                task=None,
                subject=source.url,
                args="",
            )

        return True

    def download_music(item):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DOWNLOAD_MUSIC,
            task=None,
            subject=item.link,
            args="",
        )
        return True

    def download_video(item):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DOWNLOAD_VIDEO,
            task=None,
            subject=item.link,
            args="",
        )
        return True

    def youtube_details(url):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_LINK_DETAILS, task=None, subject=url, args=""
        )
        return True

    def link_add(url, source):
        existing = LinkDataModel.objects.filter(link=url)
        if len(existing) > 0:
            return False

        if (
            len(
                BackgroundJob.objects.filter(
                    job=BackgroundJob.JOB_LINK_ADD, subject=url
                )
            )
            == 0
        ):
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_LINK_ADD,
                task=None,
                subject=url,
                args=str(source.id),
            )

    def write_daily_data_range(date_start=date.today(), date_stop=date.today()):
        from datetime import timedelta

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

                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_WRITE_DAILY_DATA,
                    task=None,
                    subject=str_date,
                    args="",
                )
                sent = True

            return sent
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Daily data: {} {}".format(str(e), error_text)
            )

    def write_daily_data(input_date):
        bj = BackgroundJob.objects.create(
            job=BackgroundJob.JOB_WRITE_DAILY_DATA,
            task=None,
            subject=input_date,
            args="",
        )
        return True

    def write_daily_data_str(start="2022-01-01", stop="2022-12-31"):
        try:
            date_start = datetime.strptime(start, "%Y-%m-%d").date()
            date_stop = datetime.strptime(stop, "%Y-%m-%d").date()

            BackgroundJob.write_daily_data_range(date_start, date_stop)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Daily data: {} {}".format(str(e), error_text)
            )

    def write_tag_data(tag):
        try:
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_WRITE_TOPIC_DATA, task=None, subject=tag, args=""
            )
            return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Tag data: {} {}".format(str(e), error_text)
            )

    def write_bookmarks():
        try:
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_WRITE_BOOKMARKS, task=None, subject="", args=""
            )
            return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Write bookmarks: {} {}".format(str(e), error_text)
            )

    def link_archive(link_url):
        try:
            archive_items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_LINK_ARCHIVE
            )
            if len(archive_items) < 100:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_LINK_ARCHIVE,
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
        try:
            BackgroundJob.objects.create(
                job=BackgroundJob.JOB_LINK_DOWNLOAD,
                task=None,
                subject=link_url,
                args="",
            )
            return True
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Link download: {} {}".format(str(e), error_text)
            )

    def push_to_repo():
        try:
            items = BackgroundJob.objects.filter(
                job=BackgroundJob.JOB_PUSH_TO_REPO, subject=""
            )
            if len(items) == 0:
                BackgroundJob.objects.create(
                    job=BackgroundJob.JOB_PUSH_TO_REPO, task=None, subject="", args=""
                )
                return True
            elif len(items) > 1:
                for item in items:
                    item.delete()
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception: Link download: {} {}".format(str(e), error_text)
            )
