from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from utils.dateutils import DateUtils

from ..models import (
    LinkDataModel,
    LinkCommentDataModel,
)
from ..configuration import Configuration

from .entries import LinkDataController


class LinkCommentDataController(LinkCommentDataModel):
    class Meta:
        proxy = True

    def can_user_add_comment(link_id, user):
        if not user.is_authenticated:
            return

        now = datetime.now()
        time_start = now - timedelta(days=1)
        time_stop = now

        link = LinkDataModel.objects.get(id=link_id)

        criterion0 = Q(user_object=user, entry_object=link)
        criterion1 = Q(date_published__range=[time_start, time_stop])
        criterion2 = Q(date_edited__range=[time_start, time_stop])

        comments = LinkCommentDataModel.objects.filter(
            criterion0 & (criterion1 | criterion2)
        )

        conf = Configuration.get_object().config_entry

        if comments.count() > conf.number_of_comments_per_day:
            return False

        return True

    def add(user, entry, data):
        if not user:
            return

        if not entry:
            return

        if not user.is_authenticated:
            return

        date_published = data["date_published"]
        comments = LinkCommentDataModel.objects.filter(
            user_object=user, entry_object=entry, date_published=date_published
        )

        if comments.count() == 0:
            reply_id = None
            if "reply_id" in data:
                reply_id = data["reply_id"]

            if "date_edited" not in data:
                data["date_edited"] = DateUtils.get_datetime_now_utc()

            return LinkCommentDataModel.objects.create(
                comment=data["comment"],
                date_published=data["date_published"],
                date_edited=data["date_edited"],
                entry_object=entry,
                user_object=user,
                reply_id=reply_id,
            )

    def save_comment(data):
        """
        TODO remove or refactor with the function above
        """
        entry = None

        if "entry_object" in data:
            entry = data["entry_object"]

        if "entry_id" in data:
            entry_id = data["entry_id"]
            entry = LinkDataController.objects.get(id=entry_id)

        if LinkCommentDataController.is_html_contents(data["comment"]):
            return

        user = data["user"]

        return LinkCommentDataController.add(user, entry, data)

    def is_html_contents(text):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "html.parser")
        tags = soup.find_all()
        return len(tags) > 0
