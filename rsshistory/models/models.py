"""
"""

import traceback
from datetime import datetime, date
import os

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


class DataExport(models.Model):
    EXPORT_TYPE_GIT = "export-type-git"
    EXPORT_TYPE_LOC = "export-type-loc"

    # fmt: off
    EXPORT_TYPE_CHOICES = (
        (EXPORT_TYPE_LOC, EXPORT_TYPE_LOC,),
        (EXPORT_TYPE_GIT, EXPORT_TYPE_GIT,),
    )
    # fmt: on

    EXPORT_DAILY_DATA = "export-dtype-daily-data"
    EXPORT_BOOKMARKS = "export-dtype-bookmarks"

    # fmt: off
    EXPORT_DATA_CHOICES = (
        (EXPORT_DAILY_DATA, EXPORT_DAILY_DATA,),
        (EXPORT_BOOKMARKS, EXPORT_BOOKMARKS,),
    )
    # fmt: on

    enabled = models.BooleanField(default=True)
    export_type = models.CharField(max_length=1000, choices=EXPORT_TYPE_CHOICES)
    export_data = models.CharField(max_length=1000, choices=EXPORT_DATA_CHOICES)
    local_path = models.CharField(max_length=1000)
    remote_path = models.CharField(max_length=1000)
    user = models.CharField(default="", max_length=2000, null=True)
    password = models.CharField(default="", max_length=2000, null=True)
