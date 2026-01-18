from django.db import models
from django.conf import settings
from django.db import DataError 

from datetime import timedelta
from utils.dateutils import DateUtils
from webtoolkit import RemoteServer, RemoteUrl, UrlLocation
import webtoolkit

from ..apps import LinkDatabase
from .entries import LinkDataModel
from .system import AppLogging


class SocialData(models.Model):
    entry = models.OneToOneField(
        LinkDataModel,
        on_delete=models.CASCADE,
    )

    thumbs_up = models.BigIntegerField(
        null=True,
        blank=True,
    )

    thumbs_down = models.BigIntegerField(
        null=True,
        blank=True,
    )

    view_count = models.BigIntegerField(
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

    stars = models.BigIntegerField(
        null=True,
        blank=True,
    )

    followers_count = models.BigIntegerField(
        null=True,
        blank=True,
    )

    date_updated = models.DateTimeField(auto_now=True, help_text="Date of update")

    def is_supported(entry):
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry
        if not config.enable_social_data:
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
        """
        Returns social data from memory, or adds social data job
        """
        from ..configuration import Configuration
        from ..controllers import BackgroundJobController

        social = SocialData.get_from_model(entry)
        if social:
            return social

        if not SocialData.is_supported(entry):
            return

        BackgroundJobController.link_download_social_data(entry)

    def update(entry):
        """
        Adds entry social data from web server
        """
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
        """
        Returns social data from model
        """
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry

        social_datas = SocialData.objects.filter(entry=entry)
        if social_datas.exists():
            social_data = social_datas[0]

            return social_data

    def get_from_server(entry):
        """
        Returns social data from server
        """
        from ..configuration import Configuration
        from ..controllers import SystemOperationController

        config = Configuration.get_object().config_entry

        if config.remote_webtools_server_location:
            controller = SystemOperationController()
            if controller.is_remote_server_down():
                raise IOError("Remote server is down")

            link = config.remote_webtools_server_location
            remote_server = RemoteServer(link)
            index = 0
            while True:
                index += 1
                if index > 4:
                    raise IOError(f"Could not obtain response from server about link entry ID:{entry.id} entry link:{entry.link} ")

                json_obj = remote_server.get_socialj(url=entry.link)
                if not json_obj:
                    raise IOError("Invalid social data response from remote server - no json object")

                if len(json_obj) == 0:
                    raise IOError("Invalid social data response from remote server - json object length is null")

                if isinstance(json_obj, list):
                    # it should be map, not list
                    url = RemoteUrl(url=entry.link, all_properties=json_obj)
                    status_code = url.get_status_code()
                    if status_code == webtoolkit.HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS:
                        continue

                    raise IOError(f"Invalid social data response from remote server - a list. Entry id:{entry.id} link:{entry.link} status_code:{status_code}")

                break

            if SocialData.is_all_none(json_obj):
                return

            json_obj["entry"] = entry
            return json_obj

    def is_all_none(json_obj):
        """
        Returns indication if json object elements are all true
        """
        # indicator of unsupported on crawler buddy
        all_values_are_none = True
        for key, value in json_obj.items():
            if value is not None:
                all_values_are_none = False

        return all_values_are_none

    def cleanup(cfg=None):
        """
        Cleans up the table
        """
        from ..configuration import Configuration

        config = Configuration.get_object().config_entry

        BATCH_SIZE = 1000

        if config.enable_social_data:
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

        if not config.enable_social_data:
            SocialData.truncate(cfg)

        return True

    def truncate(cfg=None):
        """
        Truncates the table
        """
        BATCH_SIZE = 1000

        social_datas = SocialData.objects.all()
        social_datas.delete()

        # while social_datas.exists():
        #    social_datas[:BATCH_SIZE].delete()
