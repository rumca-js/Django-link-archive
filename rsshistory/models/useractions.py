"""
"""

import traceback
from datetime import datetime, date
import os

from django.db import models
from django.urls import reverse

from ..apps import LinkDatabase
from .entries import LinkDataModel
from .system import PersistentInfo


class LinkTagsDataModel(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields

    link = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    date = models.DateTimeField(auto_now_add=True)
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

    def process_tag_string(tag_string):
        tags_set = set()
        tags = tag_string.split(LinkTagsDataModel.get_delim())
        for tag in tags:
            tag = str(tag).strip()
            tag = tag.lower()
            if tag != "":
                tags_set.add(tag)

        return tags_set

    def set_tags(data):
        """
        tags is in form tag1,tag2
        expecte author also
        """
        data["tags"] = LinkTagsDataModel.process_tag_string(data["tag"])
        return LinkTagsDataModel.set_tags_map(data)

    def set_tag(entry, tag_name, author=""):
        if not entry:
            PersistentInfo.error("Incorrect call of tags, entry does not exist")

        objs = LinkTagsDataModel.objects.filter(
            link_obj=entry, author=author, tag=tag_name
        )

        if objs.count() == 0:
            LinkTagsDataModel.objects.create(
                link=entry.link, author=author, tag=tag_name, link_obj=entry
            )

    def set_tags_map(data):
        """
        Tags is a container
        """
        author = data["author"]

        link = None
        if "link" in data:
            link = data["link"]
        entry = None

        if "entry" in data:
            entry = data["entry"]

        tag_objs = None

        if entry:
            tag_objs = LinkTagsDataModel.objects.filter(author=author, link_obj=entry)
        elif link:
            tag_objs = LinkTagsDataModel.objects.filter(author=author, link=link)
        else:
            PersistentInfo.info("Missing information about entry")
            return

        if tag_objs.exists():
            tag_objs.delete()

        tags_set = data["tags"]

        if link:
            entries = LinkDataModel.objects.filter(link=link)
            if entries.count() == 0:
                PersistentInfo.error("Invalid tag call")
                return
            entry = entries[0]

        for tag in tags_set:
            LinkTagsDataModel.objects.create(
                link=entry.link, author=author, tag=tag, link_obj=entry
            )


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

        BackgroundJobController.entry_update_data(entry)

        return ob


class LinkCommentDataModel(models.Model):
    author = models.CharField(max_length=1000)
    comment = models.TextField(max_length=3000)
    date_published = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(null=True)
    reply_id = models.IntegerField(null=True)

    link_obj = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    def get_comment(self):
        from ..webtools import InputContent

        return InputContent(self.comment).htmlify()