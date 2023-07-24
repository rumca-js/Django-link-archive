"""
"""

import traceback
from datetime import datetime, date

from django.db import models
from django.urls import reverse

from ..apps import LinkDatabase
from .linkmodels import LinkDataModel
from .appmodels import PersistentInfo, ConfigurationEntry


class RssSourceExportHistory(models.Model):
    date = models.DateField(unique=True, null=False)

    class Meta:
        ordering = ["-date"]

    def is_update_required():
        from ..dateutils import DateUtils

        try:
            ob = ConfigurationEntry.get()
            if not ob.is_bookmark_repo_set() and not ob.is_daily_repo_set():
                return

            yesterday = DateUtils.get_date_yesterday()

            history = RssSourceExportHistory.objects.filter(date=yesterday)

            if len(history) != 0:
                return False
            return True

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Exception for update: {0} {1}".format(str(e), error_text)
            )

    def get_safe():
        return RssSourceExportHistory.objects.all()[:100]


class LinkTagsDataModel(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields

    link = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    date = models.DateTimeField(default=datetime.now)
    tag = models.CharField(max_length=1000)

    link_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="tags",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-date"]

    def get_delim():
        return ","

    def join_elements(elements):
        tag_string = ""
        for element in elements:
            if tag_string == "":
                tag_string = element.tag
            else:
                tag_string += LinkTagsDataModel.get_delim() + " " + element.tag

        return tag_string

    def get_author_tag_string(author, link):
        current_tags_objs = LinkTagsDataModel.objects.filter(link=link, author=author)

        if current_tags_objs.exists():
            return LinkTagsDataModel.join_elements(current_tags_objs)


class LinkVoteDataModel(models.Model):
    author = models.CharField(max_length=1000)
    vote = models.IntegerField(default=0)

    link_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="votes",
        null=True,
        blank=True,
    )


class LinkCommentDataModel(models.Model):
    author = models.CharField(max_length=1000)
    comment = models.TextField(max_length=3000)
    date_published = models.DateTimeField(default=datetime.now)
    date_edited = models.DateTimeField(null=True)
    reply_id = models.IntegerField(null=True)

    link_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )


class Domains(models.Model):
    domain = models.CharField(max_length=1000)
    date_created = models.DateTimeField(default=datetime.now)
    date_last = models.DateTimeField(default=datetime.now)

    class Meta:
        ordering = ["domain"]

    def add(domain_text):
        if domain_text.find("/") >= 0:
            from ..webtools import Page
            p = Page(domain_text)
            domain_text = p.get_domain_only()

        objs = Domains.objects.filter(domain = domain_text)
        if len(objs) == 0:
            Domains.objects.create(domain = domain_text)
        else:
            from ..dateutils import DateUtils
            obj = objs[0]
            obj.date_last = DateUtils.get_datetime_now_utc()
            obj.save()


""" YouTube meta cache """


class YouTubeMetaCache(models.Model):
    url = models.CharField(max_length=1000, help_text="url", unique=False)
    details_json = models.CharField(max_length=1000, help_text="details_json")
    dead = models.BooleanField(default=False, help_text="dead")

    link_yt_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.SET_NULL,
        related_name="link_yt",
        null=True,
        blank=True,
    )


class YouTubeReturnDislikeMetaCache(models.Model):
    url = models.CharField(max_length=1000, help_text="url", unique=False)
    return_dislike_json = models.CharField(
        max_length=1000, help_text="return_dislike_json"
    )
    dead = models.BooleanField(default=False, help_text="dead")

    link_rd_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.SET_NULL,
        related_name="link_rd",
        null=True,
        blank=True,
    )
