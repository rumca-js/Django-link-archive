from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    LinkDataModel,
    LinkCommentDataModel,
)
from .entries import LinkDataController
from ..configuration import Configuration


class LinkCommentDataController(LinkCommentDataModel):
    class Meta:
        proxy = True

    def can_user_add_comment(link_id, user_name):
        now = datetime.now()
        time_start = now - timedelta(days=1)
        time_stop = now

        link = LinkDataModel.objects.get(id=link_id)

        criterion0 = Q(author=user_name, link_obj=link)
        criterion1 = Q(date_published__range=[time_start, time_stop])
        criterion2 = Q(date_edited__range=[time_start, time_stop])

        comments = LinkCommentDataModel.objects.filter(
            criterion0 & (criterion1 | criterion2)
        )

        conf = Configuration.get_object().config_entry

        if comments.count() > conf.number_of_comments_per_day:
            return False

        return True

    def save_comment(data):
        entry = LinkDataController.objects.get(id=data["link_id"])

        if LinkDataController.is_html_contents(data["comment"]):
            return

        return LinkCommentDataModel.objects.create(
            author=data["author"],
            comment=data["comment"],
            date_published=data["date_published"],
            link_obj=entry,
        )

    def is_html_contents(text):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(text, "html.parser")
        tags = soup.find_all()
        return len(tags) > 0
