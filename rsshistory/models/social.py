
from django.db import models
from django.conf import settings

from datetime import timedelta
from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from .entries import LinkDataModel
from ..controllers import (
    SystemOperationController,
)
from ..webtools import (
    RemoteServer,
)


class SocialData(models.Model):
    entry = models.OneToOneField(
        LinkDataModel,
        on_delete=models.CASCADE,
    )

    thumbs_up = models.IntegerField(
        null=True,
    )

    thumbs_down = models.IntegerField(
        null=True,
    )

    view_count = models.IntegerField(
        null=True,
    )

    rating = models.FloatField(
        null=True,
        help_text="For various sites rating has different meaning.",
    )

    upvote_ratio = models.FloatField(
        null=True,
        help_text="(Thumbs up - thumbs diff) / all thumbs.",
    )

    upvote_diff = models.FloatField(
        null=True,
        help_text="Thumbs up - thumbs diff.",
    )

    upvote_view_ratio = models.FloatField(
        null=True,
        help_text="(Thumbs up - thumbs diff) / view count.",
    )

    stars = models.IntegerField(
        null=True,
    )

    followers_count = models.IntegerField(
        null=True,
    )

    date_updated = models.DateTimeField(
        auto_now=True,
        help_text="Date of update"
    )

    def get(entry):
        social = SocialData.get_from_model(entry)
        if social:
            return social

        social = SocialData.get_from_server(entry)
        if social:
            return social

        SocialData.objects.create(entry=entry)

    def get_from_model(entry):
        from ..configuration import Configuration
        config = Configuration.get_object().config_entry

        social_datas = SocialData.objects.filter(entry = entry)
        if social_datas.exists():
            social_data = social_datas[0]

            return social_data

    def get_from_server(entry):
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry

        if config.remote_webtools_server_location:
            controller = SystemOperationController()
            if controller.is_remote_server_down():
                return

            link = config.remote_webtools_server_location
            remote_server = RemoteServer(link)

            json_obj = remote_server.get_socialj(entry.link)
            if not json_obj:
                return

            if len(json_obj) == 0:
                return

            json_obj["entry"] = entry

            return SocialData.objects.create(**json_obj)

    def cleanup(cfg=None):
        from ..configuration import Configuration
        config = Configuration.get_object().config_entry

        BATCH_SIZE = 1000

        if config.keep_social_data:
            five_days_ago = DateUtils.get_datetime_now_utc() - timedelta(days=config.days_to_remove_social_data)

            while True:
                old_ids = list(
                    SocialData.objects
                    .filter(date_updated__lt=five_days_ago)
                    .values_list('id', flat=True)[:BATCH_SIZE]
                )
                if not old_ids:
                    break
                SocialData.objects.filter(id__in=old_ids).delete()

        if not config.keep_social_data:
            SocialData.truncate(cfg)

    def truncate(cfg=None):
        BATCH_SIZE = 1000

        social_datas = SocialData.objects.all()
        social_datas.delete()

        #while social_datas.exists():
        #    social_datas[:BATCH_SIZE].delete()
