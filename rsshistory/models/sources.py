from django.db import models
from django.urls import reverse


class SourceOperationalData(models.Model):
    url = models.CharField(max_length=2000, unique=True)
    date_fetched = models.DateTimeField(null=True)
    import_seconds = models.IntegerField(null=True)
    number_of_entries = models.IntegerField(null=True)

    class Meta:
        ordering = ["date_fetched"]


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
    language = models.CharField(max_length=10, default="en")
    favicon = models.CharField(max_length=1000, null=True)
    on_hold = models.BooleanField(default=False)
    fetch_period = models.IntegerField(default=900)
    source_type = models.CharField(
        max_length=1000, null=False, choices=SOURCE_TYPES, default=SOURCE_TYPE_RSS
    )

    class Meta:
        ordering = ["title"]

    def reset_dynamic_data():
        objs = SourceCategories.objects.all()
        objs.delete()
        objs = SourceSubCategories.objects.all()
        objs.delete()

        sources = SourceDataModel.objects.all()
        for source in sources:
            SourceCategories.add(source.category)
            SourceSubCategories.add(source.category, source.subcategory)

    dynamic_data = models.OneToOneField(
        SourceOperationalData,
        on_delete=models.SET_NULL,
        related_name="source_obj",
        null=True,
        blank=True,
    )


class SourceCategories(models.Model):
    category = models.CharField(max_length=1000, unique=True)

    class Meta:
        ordering = ["category"]

    def add(category):
        if category and category != "":
            objs = SourceCategories.objects.filter(category=category)
            if objs.count() == 0:
                SourceCategories.objects.create(category=category)


class SourceSubCategories(models.Model):
    category = models.CharField(max_length=1000, default="")
    subcategory = models.CharField(max_length=1000)

    class Meta:
        ordering = ["category", "subcategory"]

    def add(category, subcategory):
        if category and category != "" and subcategory and subcategory != "":
            objs = SourceSubCategories.objects.filter(
                category=category, subcategory=subcategory
            )
            if objs.count() == 0:
                SourceSubCategories.objects.create(
                    category=category, subcategory=subcategory
                )
