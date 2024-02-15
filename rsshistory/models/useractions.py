"""
"""

import traceback
from datetime import datetime, date
import os
import time

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from .entries import LinkDataModel
from .system import PersistentInfo


class LinkTagsDataModel(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields

    link = models.CharField(max_length=1000)
    user = models.CharField(max_length=1000)
    date = models.DateTimeField(auto_now_add=True)
    tag = models.CharField(max_length=1000)

    user_object = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name)+'_user_tags',
        null=True)

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

    def get_user_tag_string(user, link):
        current_tags_objs = LinkTagsDataModel.objects.filter(link=link, user=user.username)

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

    def set_tag(entry, tag_name, user=None):
        if not entry:
            PersistentInfo.error("Incorrect call of tags, entry does not exist")

        user_name = ""
        if user:
            user_name = user.username

        objs = LinkTagsDataModel.objects.filter(
            link_obj=entry, user=user_name, tag=tag_name
        )

        if objs.count() == 0:
            LinkTagsDataModel.objects.create(
                link=entry.link, user=user, tag=tag_name, link_obj=entry, user_object=user
            )

    def set_tags_map(data):
        """
        Tags is a container
        """
        user = data["user"]

        link = None
        if "link" in data:
            link = data["link"]
        entry = None

        if "entry" in data:
            entry = data["entry"]

        tag_objs = None

        if entry:
            tag_objs = LinkTagsDataModel.objects.filter(user=user.username, link_obj=entry)
        elif link:
            tag_objs = LinkTagsDataModel.objects.filter(user=user.username, link=link)
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
                link=entry.link, user=user.username, tag=tag, link_obj=entry, user_object=user
            )

    def cleanup():
        for q in LinkTagsDataModel.objects.filter(user_object__isnull=True):
            users = User.objects.filter(username = q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.error("Cannot find user '{}'".format(q.user))
                q.delete()
                time.sleep(0.5)


class LinkVoteDataModel(models.Model):
    user = models.CharField(max_length=1000)
    vote = models.IntegerField(default=0)

    user_object = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name)+'_user_votes',
        null=True)

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
        user = input_data["user"]
        vote = input_data["vote"]

        entry = LinkDataModel.objects.get(id=link_id)

        votes = LinkVoteDataModel.objects.filter(user=user, link_obj=entry)
        votes.delete()

        ob = LinkVoteDataModel.objects.create(
            user=user.username,
            vote=vote,
            link_obj=entry,
            user_object=user,
        )

        # TODO this should be a background task
        entry.update_calculated_vote()

        BackgroundJobController.entry_update_data(entry)

        return ob

    def cleanup():
        for q in LinkVoteDataModel.objects.filter(user_object__isnull=True):
            users = User.objects.filter(username = q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.error("Cannot find user '{}'".format(q.user))
                q.delete()
                time.sleep(0.5)


class LinkCommentDataModel(models.Model):
    user = models.CharField(max_length=1000)
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

    user_object = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name)+'_user_comments',
        null=True)

    def get_comment(self):
        from ..webtools import InputContent

        return InputContent(self.comment).htmlify()

    def cleanup():
        for q in LinkCommentDataModel.objects.filter(user_object__isnull=True):
            users = User.objects.filter(username = q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.error("Cannot find user '{}'".format(q.user))
                q.delete()
                time.sleep(0.5)
