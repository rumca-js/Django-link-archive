"""
API needs to check user privileges.

Do not include model.User, include it only in functions.
Otherwise running tests might not work in postgresql.
https://github.com/pinax/django-user-accounts/issues/179
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
from .system import AppLogging


class UserTags(models.Model):
    # https://stackoverflow.com/questions/14066531/django-model-with-unique-combination-of-two-fields
    date = models.DateTimeField(auto_now_add=True)
    tag = models.CharField(max_length=1000)

    user_object = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_user_tags",
        null=True,
    )

    entry_object = models.ForeignKey(
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
                tag_string += UserTags.get_delim() + " " + element.tag

        return tag_string

    def get_user_tag_string(user, entry):
        current_tags_objs = UserTags.objects.filter(
            entry_object=entry, user_object=user
        )

        if current_tags_objs.exists():
            return UserTags.join_elements(current_tags_objs)

    def process_tag_string(tag_string):
        tags_set = set()
        tags = tag_string.split(UserTags.get_delim())
        for tag in tags:
            tag = str(tag).strip()
            tag = tag.lower()
            if tag != "":
                tags_set.add(tag)

        return tags_set

    def set_tag(entry, tag_name, user=None):
        """
        Adds additional tag
        """
        if not user:
            return

        if not entry:
            AppLogging.error("Incorrect call of tags, entry does not exist")

        user_name = user.username

        objs = UserTags.objects.filter(
            entry_object=entry, user_object=user, tag=tag_name
        )

        if objs.count() == 0:
            UserTags.objects.create(entry_object=entry, user_object=user, tag=tag_name)

    def set_tags(data):
        """
        Removes all other tags, sets only tags in data
        """
        data["tags"] = UserTags.process_tag_string(data["tag"])
        return UserTags.set_tags_map(data)


    def set_tags_map(data):
        """
        Removes all other tags, sets only tags in data
        """
        user = None
        if "user" in data:
            user = data["user"]

        elif "user_id" in data:
            user_id = data["user_id"]
            user = User.objects.get(id = user_id)

        entry = None

        if "entry" in data:
            entry = data["entry"]
        elif "entry_id" in data:
            entry_id = data["entry_id"]
            entry = LinkDataModel.objects.get(id=entry_id)

        tag_objs = None

        if entry:
            tag_objs = UserTags.objects.filter(user_object=user, entry_object=entry)

            if tag_objs.exists():
                tag_objs.delete()
        else:
            AppLogging.info("Missing entry object")
            return

        tags_set = data["tags"]

        for tag in tags_set:
            UserTags.objects.create(tag=tag, entry_object=entry, user_object=user)

    def cleanup():
        for q in UserTags.objects.filter(user_object__isnull=True):
            if q.user_object:
                users = User.objects.filter(id=q.user_object.id)
                if users.count() > 0:
                    q.user_object = users[0]
                    q.save()
                    continue

            users = User.objects.filter(is_superuser=True)
            if users.count() > 0:
                user = users[0]
                q.user_object = user
                q.save()

                #LinkDatabase.error("Cannot find user '{}'".format(q.user_object.id))
                #q.delete()
                #time.sleep(0.5)


class UserVotes(models.Model):
    user = models.CharField(max_length=1000)
    vote = models.IntegerField(default=0)

    user_object = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_user_votes",
        null=True,
    )

    entry_object = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="votes",
        null=True,
        blank=True,
    )

    def add(user, entry, vote):
        if not user:
            return
    
        if not user.is_authenticated:
            return

        votes = UserVotes.objects.filter(user_object = user, entry_object = entry)

        if votes.count() == 0:
            from ..controllers import BackgroundJobController

            votes = UserVotes.objects.filter(user=user, entry_object=entry)
            votes.delete()

            ob = UserVotes.objects.create(
                vote=vote,
                entry_object=entry,
                user_object=user,
            )
        else:
            ob = votes[0]
            ob.vote = vote
            ob.save()

        # TODO this should be a background task
        entry.update_calculated_vote()

        from ..controllers import BackgroundJobController
        BackgroundJobController.entry_update_data(entry)

        return ob

    def get_user_vote(user, entry):
        votes = UserVotes.objects.filter(user_object=user, entry_object=entry)
        if votes.count() > 0:
            vote = votes[0].vote
            return vote

        return 0

    def save_vote(input_data):
        entry_id = input_data["entry_id"]
        user = input_data["user"]
        vote = input_data["vote"]

        entry = LinkDataModel.objects.get(id=entry_id)

        return UserVotes.add(user, entry, vote)

    def cleanup():
        # recreate missing entries, from votes alone
        for entry in LinkDataModel.objects.filter(page_rating_votes__gt = 0):
            votes = UserVotes.objects.filter(entry_object = entry)
            if votes.count() == 0:
                users = User.objects.filter(is_superuser=True)
                if users.count() > 0:
                    UserVotes.add(users[0], entry, entry.page_rating_votes)

        # reset missing user object
        for q in UserVotes.objects.filter(user_object__isnull=True):
            users = User.objects.filter(username=q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.error("Cannot find user '{}'".format(q.user))
                q.delete()
                time.sleep(0.5)


class LinkCommentDataModel(models.Model):
    """
    TODO change name to UserComments. Cannot do that right now. Django says no.
    """

    comment = models.TextField(max_length=3000)
    date_published = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(null=True)
    # id of previous comment
    reply_id = models.IntegerField(null=True)

    entry_object = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )

    user_object = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_user_comments",
        null=True,
    )

    def get_comment(self):
        from ..webtools import InputContent

        return InputContent(self.comment).htmlify()

    def cleanup():
        for q in LinkCommentDataModel.objects.filter(user_object__isnull=True):
            users = User.objects.filter(username=q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.error("Cannot find user '{}'".format(q.user))
                q.delete()
                time.sleep(0.5)


class UserBookmarks(models.Model):
    date_bookmarked = models.DateTimeField(auto_now_add=True)

    entry_object = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="bookmarks",
        null=True,
        blank=True,
    )

    user_object = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_user_bookmarks",
        null=True,
    )

    def add(user, entry):
        if not user:
            return

        if not user.is_authenticated:
            return

        objs = UserBookmarks.objects.filter(user_object=user, entry_object=entry)
        if objs.count() == 0:
            UserBookmarks.objects.create(user_object=user, entry_object=entry)

    def remove(user, entry):
        if not user.is_authenticated:
            return

        bookmarks = UserBookmarks.objects.filter(user_object=user, entry_object=entry)
        bookmarks.delete()

    def remove_entry(entry):
        bookmarks = UserBookmarks.objects.filter(entry_object=entry)
        bookmarks.delete()

    def is_bookmarked(entry):
        bookmarks = UserBookmarks.objects.filter(entry_object=entry)
        for bookmark in bookmarks:
            if bookmark.user_object.is_staff:
                return True

        return False

    def cleanup():
        entries = LinkDataModel.objects.filter(bookmarked=True)
        for entry in entries:
            if not UserBookmarks.is_bookmarked(entry):
                users = User.objects.filter(is_superuser=True)

                if users.count() > 0:
                    UserBookmarks.add(users[0], entry)
