from django.db import models
from django.urls import reverse

from ..webtools import DomainAwarePage

from ..apps import LinkDatabase


class SourceDataModel(models.Model):
    SOURCE_TYPE_RSS = "BaseRssPlugin"
    SOURCE_TYPE_JSON = "BaseSourceJsonPlugin"
    SOURCE_TYPE_PARSE = "BaseParsePlugin"
    SOURCE_TYPE_YOUTUBE = "YouTubeChannelPlugin"

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    enabled = models.BooleanField(default=True)
    # main category
    category = models.CharField(max_length=1000, blank=True)
    # main subcategory
    subcategory = models.CharField(max_length=1000, blank=True)
    export_to_cms = models.BooleanField(
        default=True, help_text="Entries from this source are eligible to export to CMS"
    )
    remove_after_days = models.IntegerField(
        default=0, help_text="Remove entries after [x] days"
    )
    language = models.CharField(max_length=10, blank=True)  # inherited into entries
    age = models.IntegerField(default=0)  # inherited into entries
    favicon = models.CharField(max_length=1000, null=True)
    fetch_period = models.IntegerField(
        default=900, help_text="Source is checked for new data after [x] seconds"
    )
    source_type = models.CharField(max_length=1000, null=False, default=SOURCE_TYPE_RSS)
    auto_tag = models.CharField(
        max_length=1000, blank=True, help_text="Automatic tag for new entries"
    )

    proxy_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Proxy location for the source. Proxy location will be used instead of normal processing.",
    )

    class Meta:
        ordering = ["-enabled", "title"]

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:source-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

    def reset_dynamic_data():
        objs = SourceCategories.objects.all()
        objs.delete()
        objs = SourceSubCategories.objects.all()
        objs.delete()

        sources = SourceDataModel.objects.all()
        for source in sources:
            SourceCategories.add(source.category)
            SourceSubCategories.add(source.category, source.subcategory)

    def get_favicon(self):
        if self.favicon:
            return self.favicon

        # returning real favicon from HTML is too long

        return DomainAwarePage(self.url).get_domain() + "/favicon.ico"


class SourceOperationalData(models.Model):
    date_fetched = models.DateTimeField(null=True)
    import_seconds = models.IntegerField(null=True)
    number_of_entries = models.IntegerField(null=True)
    page_hash = models.BinaryField(max_length=30, null=True)  # TODO Move to entry
    consecutive_errors = models.IntegerField(default=0)

    class Meta:
        ordering = ["date_fetched"]

    source_obj = models.OneToOneField(
        SourceDataModel,
        on_delete=models.CASCADE,
        related_name="dynamic_data",
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

    def get(category):
        objs = SourceCategories.objects.filter(category=category)
        if objs.count() != 0:
            return objs[0]


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

    def get(category, subcategory):
        objs = SourceSubCategories.objects.filter(
            category=category, subcategory=subcategory
        )
        if objs.count() != 0:
            return objs[0]
