from django.db import models

from utils.dateutils import DateUtils
from .sources import SourceDataModel


class ReadMarkers(models.Model):
    """
    """
    source_obj = models.OneToOneField(
        SourceDataModel,
        on_delete=models.CASCADE,
        related_name="marker",
        null=True,
        blank=True,
    )
    read_date = models.DateTimeField(null=True)

    def get(source = None):
        if source is None:
            return ReadMarkers.get_general()
        else:
            return ReadMarkers.get_source(source)

    def get_general():
        read_markers = ReadMarkers.objects.filter(source_obj = True)
        if read_markers.exists():
            return read_markers[0]

    def get_source(source):
        markers = source.marker.all()
        if markers.exists():
            return marker[0]

    def set_general():
        marker = ReadMarkers.get_general()
        if not marker:
            m = ReadMarkers(read_date = DateUtils.get_datetime_now_utc())
            m.save()
        else:
            general.read_date = DateUtils.get_datetime_utc()
            general.save()

    def set_source(source):
        marker = ReadMarkers.get_source(source)
        if not marker:
            m = ReadMarkers(read_date = DateUtils.get_datetime_now_utc(), source_obj = source)
            m.save()
        else:
            general.read_date = DateUtils.get_datetime_now_utc()
            general.save()
