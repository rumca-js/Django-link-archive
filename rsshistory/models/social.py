from django.db import models
from django.conf import settings
from django.db import DataError 

from datetime import timedelta
from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from .entries import LinkDataModel
from ..webtools import (
    RemoteServer,
    UrlLocation,
)
from .system import AppLogging


class SocialData(models.Model):
    entry = models.OneToOneField(
        LinkDataModel,
        on_delete=models.CASCADE,
    )

    thumbs_up = models.IntegerField(
        null=True,
        blank=True,
    )

    thumbs_down = models.IntegerField(
        null=True,
        blank=True,
    )

    view_count = models.IntegerField(
        null=True,
        blank=True,
    )

    rating = models.FloatField(
        null=True,
        blank=True,
        help_text="For various sites rating has different meaning.",
    )

    upvote_ratio = models.FloatField(
        null=True,
        blank=True,
        help_text="(Thumbs up - thumbs diff) / all thumbs.",
    )

    upvote_diff = models.FloatField(
        null=True,
        blank=True,
        help_text="Thumbs up - thumbs diff.",
    )

    upvote_view_ratio = models.FloatField(
        null=True,
        blank=True,
        help_text="(Thumbs up - thumbs diff) / view count.",
    )

    stars = models.IntegerField(
        null=True,
        blank=True,
    )

    followers_count = models.IntegerField(
        null=True,
        blank=True,
    )

    date_updated = models.DateTimeField(auto_now=True, help_text="Date of update")

    def is_supported(entry):
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry
        if not config.keep_social_data:
            return False

        page = UrlLocation(entry.link)
        domain = page.get_domain()
        if not domain:
            return False

        if domain.find("youtube.com") >= 0:
            return True
        if domain.find("github.com") >= 0:
            return True
        if domain.find("reddit.com") >= 0:
            return True
        if domain.find("news.ycombinator.com") >= 0:
            return True

        return False

    def get(entry):
        from ..configuration import Configuration
        from ..controllers import BackgroundJobController

        social = SocialData.get_from_model(entry)
        if social:
            return social

        if not SocialData.is_supported(entry):
            return

        BackgroundJobController.link_download_social_data(entry)

    def update(entry):
        new_social = SocialData.get_from_server(entry)
        if new_social:
            social_data = SocialData.objects.filter(entry=entry)
            if social_data.exists():
                social_data.delete()

            try:
                return SocialData.objects.create(**new_social)
            except DataError as E:
                AppLogging.exc(E, info_text = "Data:{}".format(new_social))

    def get_from_model(entry):
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry

        social_datas = SocialData.objects.filter(entry=entry)
        if social_datas.exists():
            social_data = social_datas[0]

            return social_data

    def get_from_server(entry):
        from ..configuration import Configuration
        from ..controllers import SystemOperationController

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

            # indicator of unsupported on crawler buddy
            all_values_are_none = True
            for key, value in json_obj.items():
                if value is not None:
                    all_values_are_none = False

            if all_values_are_none:
                return

            json_obj["entry"] = entry
            return json_obj

    def cleanup(cfg=None):
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry

        BATCH_SIZE = 1000

        if config.keep_social_data:
            if config.days_to_remove_social_data == 0:
                return

            five_days_ago = DateUtils.get_datetime_now_utc() - timedelta(
                days=config.days_to_remove_social_data
            )

            while True:
                old_ids = list(
                    SocialData.objects.filter(
                        date_updated__lt=five_days_ago
                    ).values_list("id", flat=True)[:BATCH_SIZE]
                )
                if not old_ids:
                    break
                SocialData.objects.filter(id__in=old_ids).delete()

        if not config.keep_social_data:
            SocialData.truncate(cfg)

        return True

    def truncate(cfg=None):
        BATCH_SIZE = 1000

        social_datas = SocialData.objects.all()
        social_datas.delete()

        # while social_datas.exists():
        #    social_datas[:BATCH_SIZE].delete()
