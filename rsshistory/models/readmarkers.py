from django.db import models
from django.conf import settings

from utils.dateutils import DateUtils
from .sources import SourceDataModel
from ..apps import LinkDatabase


class ReadMarkers(models.Model):
    """
    Used to indicate what has been read, and what has not
    """
    read_date = models.DateTimeField(null=True)

    source = models.OneToOneField(
        SourceDataModel,
        on_delete=models.CASCADE,
        related_name="marker",
        null=True,
        blank=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_markers",
        null=True,
    )

    def get(user, source = None):
        if source is None:
            return ReadMarkers.get_general(user)
        else:
            return ReadMarkers.get_source(user, source)

    def get_general(user):
        read_markers = ReadMarkers.objects.filter(user = user, source__isnull = True)
        if read_markers.exists():
            if read_markers.count() > 0:
                for read_marker in read_markers:
                    read_marker.delete()
            return read_markers[0]

    def get_source(user, source):
        if hasattr(source, "marker"):
            read_markers = source.marker.filter(user = user)
            if read_markers.count() > 0:
                for read_marker in read_markers:
                    read_marker.delete()

            if read_markers.exists():
                return read_markers[0]

    def set(user, source = None):
        if source:
            ReadMarkers.set_source(user, source)
        else:
            ReadMarkers.set_general(user)

    def set_general(user):
        marker = ReadMarkers.get_general(user)
        if not marker:
            m = ReadMarkers(user = user, read_date = DateUtils.get_datetime_now_utc())
            m.save()
        else:
            general.read_date = DateUtils.get_datetime_utc()
            general.save()

    def set_source(user, source):
        marker = ReadMarkers.get_source(user, source)
        if not marker:
            m = ReadMarkers(user = user, read_date = DateUtils.get_datetime_now_utc(), source = source)
            m.save()
        else:
            general.read_date = DateUtils.get_datetime_now_utc()
            general.save()
