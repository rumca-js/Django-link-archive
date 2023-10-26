"""
"""

import traceback
from datetime import datetime, date
import os

from django.db import models
from django.urls import reverse

from ..apps import LinkDatabase
from .entries import LinkDataModel
from .admin import PersistentInfo, ConfigurationEntry


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

    def save_vote(input_data):
        from ..controllers import BackgroundJobController
        link_id = input_data["link_id"]
        author = input_data["author"]
        vote = input_data["vote"]

        entry = LinkDataModel.objects.get(id=link_id)

        votes = LinkVoteDataModel.objects.filter(author=author, link_obj=entry)
        votes.delete()

        ob = LinkVoteDataModel.objects.create(
            author=author,
            vote=vote,
            link_obj=entry,
        )

        # TODO this should be a background task
        entry.update_calculated_vote()

        BackgroundJobController.update_entry_data(entry.link)

        return ob


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
