from django.db import models
from django.urls import reverse


class SourceDataModel(models.Model):
    SOURCE_TYPE_RSS = "BaseRssPlugin"
    SOURCE_TYPE_PARSE = "BaseParsePlugin"
    SOURCE_TYPE_GENEROUS_PARSE = "SourceGenerousParserPlugin"
    SOURCE_TYPE_CODEPROJECT = "CodeProjectPlugin"
    SOURCE_TYPE_INSTALKI = "InstalkiPlugin"
    SOURCE_TYPE_DIGITS_START = "SourceParseDigitsPlugin"
    SOURCE_TYPE_TVN24 = "TVN24Plugin"
    SOURCE_TYPE_SPOTIFY = "SpotifyPlugin"

    # fmt: off
    SOURCE_TYPES = (
        (SOURCE_TYPE_RSS, SOURCE_TYPE_RSS),                     #
        (SOURCE_TYPE_PARSE, SOURCE_TYPE_PARSE),                 #
        (SOURCE_TYPE_GENEROUS_PARSE, SOURCE_TYPE_GENEROUS_PARSE),                 #
        (SOURCE_TYPE_CODEPROJECT, SOURCE_TYPE_CODEPROJECT),     #
        (SOURCE_TYPE_INSTALKI, SOURCE_TYPE_INSTALKI),           #
        (SOURCE_TYPE_DIGITS_START, SOURCE_TYPE_DIGITS_START),       #
        (SOURCE_TYPE_TVN24, SOURCE_TYPE_TVN24),                 #
        (SOURCE_TYPE_SPOTIFY, SOURCE_TYPE_SPOTIFY),             #
    )
    # fmt: on

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    category = models.CharField(max_length=1000)
    subcategory = models.CharField(max_length=1000)
    dead = models.BooleanField(default=False)
    export_to_cms = models.BooleanField(default=False)
    remove_after_days = models.CharField(max_length=10, default="0")
    language = models.CharField(max_length=1000, default="en-US")
    favicon = models.CharField(max_length=1000, null=True)
    on_hold = models.BooleanField(default=False)
    fetch_period = models.IntegerField(default=900)
    source_type = models.CharField(
        max_length=1000, null=False, choices=SOURCE_TYPES, default=SOURCE_TYPE_RSS
    )

    class Meta:
        ordering = ["title"]


class SourceOperationalData(models.Model):
    url = models.CharField(max_length=2000, unique=True)
    date_fetched = models.DateTimeField(null=True)
    import_seconds = models.IntegerField(null=True)
    number_of_entries = models.IntegerField(null=True)
    source_obj = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="dynamic_data",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["date_fetched"]
