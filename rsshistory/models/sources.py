from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator,MaxValueValidator

from ..webtools import UrlLocation

from ..apps import LinkDatabase
from .credentials import Credentials


class SourceCategories(models.Model):
    name = models.CharField(max_length=1000, unique=True)

    class Meta:
        ordering = ["name"]

    def ensure(category_name):
        category = SourceCategories.get(category_name)
        if category:
            return category

        else:
            return SourceCategories.add(category_name)

    def add(category_name):
        if category_name and category_name != "":
            objs = SourceCategories.objects.filter(name=category_name)
            if not objs.exists():
                return SourceCategories.objects.create(name=category_name)

    def get(category_name):
        objs = SourceCategories.objects.filter(name=category_name)
        if objs.exists():
            return objs[0]

    def __str__(self):
        return "{}".format(
            self.name,
        )

    def cleanup():
        for category in SourceCategories.objects.all():
            if not category.sources.all().exists():
                category.delete()


class SourceSubCategories(models.Model):
    category_name = models.CharField(max_length=1000, default="")
    name = models.CharField(max_length=1000)

    category = models.ForeignKey(
        SourceCategories,
        on_delete=models.CASCADE,
        related_name="subcategories",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["category_name", "name"]

    def ensure(category_name, subcategory_name):
        subcategory = SourceSubCategories.get(category_name, subcategory_name)
        if subcategory:
            return subcategory

        else:
            return SourceSubCategories.add(category_name, subcategory_name)

    def add(category_name, subcategory_name):
        if (
            category_name
            and category_name != ""
            and subcategory_name
            and subcategory_name != ""
        ):
            category = SourceCategories.ensure(category_name)
            if not category:
                return

            objs = SourceSubCategories.objects.filter(
                category_name=category_name, name=subcategory_name
            )
            if not objs.exists():
                return SourceSubCategories.objects.create(
                    category_name=category_name,
                    name=subcategory_name,
                    category=category,
                )

    def get(category_name, subcategory_name):
        objs = SourceSubCategories.objects.filter(
            category_name=category_name, name=subcategory_name
        )
        if objs.exists():
            return objs[0]

    def __str__(self):
        return "{}".format(
            self.name,
        )

    def cleanup():
        for subcategory in SourceSubCategories.objects.all():
            if not subcategory.sources.all().exists():
                subcategory.delete()


class SourceDataModel(models.Model):
    SOURCE_TYPE_RSS = "BaseRssPlugin"
    SOURCE_TYPE_JSON = "BaseSourceJsonPlugin"
    SOURCE_TYPE_PARSE = "BaseParsePlugin"
    SOURCE_TYPE_YOUTUBE = "YouTubeChannelPlugin"
    SOURCE_TYPE_EMAIL = "EmailSourcePlugin"

    SOURCES_TYPES = (
        (SOURCE_TYPE_RSS, SOURCE_TYPE_RSS),
        (SOURCE_TYPE_JSON, SOURCE_TYPE_JSON),
        (SOURCE_TYPE_PARSE, SOURCE_TYPE_PARSE),
        (SOURCE_TYPE_YOUTUBE, SOURCE_TYPE_YOUTUBE),
        (SOURCE_TYPE_EMAIL, SOURCE_TYPE_EMAIL),
    )

    enabled = models.BooleanField(default=True)
    source_type = models.CharField(
        max_length=1000,
        null=False,
        default=SOURCE_TYPE_RSS,
        choices=SOURCES_TYPES,
    )
    url = models.CharField(
        max_length=2000,
        unique=True,
        help_text="Url of RSS feed, location to parse or Email IMAP server",
    )
    title = models.CharField(max_length=1000, blank=True, help_text="Source title")
    # main category
    category_name = models.CharField(max_length=1000, blank=True)
    # main subcategory
    subcategory_name = models.CharField(max_length=1000, blank=True)
    export_to_cms = models.BooleanField(
        default=True, help_text="Entries from this source are eligible to export to CMS"
    )
    remove_after_days = models.IntegerField(
        default=0, help_text="Remove entries after [x] days"
    )
    language = models.CharField(max_length=10, blank=True)  # inherited into entries
    age = models.IntegerField(default=0)  # inherited into entries
    favicon = models.CharField(max_length=1000, null=True, blank=True)
    fetch_period = models.IntegerField(
        default=900, help_text="Source is checked for new data after [x] seconds"
    )

    auto_tag = models.CharField(
        max_length=1000, blank=True, help_text="Automatic tag for new entries"
    )

    entries_backgroundcolor_alpha = models.FloatField(
        default=0.0,
        validators = [MinValueValidator(0), MaxValueValidator(1)],
        help_text="Background color alpha needs to be 1.0 to be visible",
    )

    entries_backgroundcolor = models.CharField(
        max_length=1000, blank=True, help_text="Background color to be applied for a source"
    )

    entries_alpha = models.FloatField(
        default=1.0,
        validators = [MinValueValidator(0), MaxValueValidator(1)],
        help_text="Alpha of entire entry",
    )

    credentials = models.ForeignKey(
        Credentials,
        on_delete=models.CASCADE,
        related_name="sources",
        blank=True,
        null=True,
    )

    category = models.ForeignKey(
        SourceCategories,
        on_delete=models.SET_NULL,
        related_name="sources",
        blank=True,
        null=True,
    )

    subcategory = models.ForeignKey(
        SourceSubCategories,
        on_delete=models.SET_NULL,
        related_name="sources",
        blank=True,
        null=True,
    )

    proxy_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Proxy location for the source. Proxy location will be used instead of normal processing.",
    )

    auto_update_favicon = models.BooleanField(default=True)

    class Meta:
        ordering = ["-enabled", "-dynamic_data__consecutive_errors", "title"]

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:source-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

    def reset_dynamic_data():
        from ..models import AppLogging

        objs = SourceSubCategories.objects.all().delete()
        objs = SourceCategories.objects.all().delete()

        sources = SourceDataModel.objects.all()
        for source in sources:
            source.category = None
            source.subcategory = None

            if (not source.category_name or source.category_name == "") and (source.subcategory_name and source.subcategory_name != ""):
                AppLogging.error("Source:{} Incorrectly defined source categories".format(source.id))
                source.save()
                continue

            category = SourceCategories.ensure(source.category_name)
            if not category:
                AppLogging.error("Source:{} Cannot create category with name {}".format(source.id, source.category_name))
                source.save()
                continue

            subcategory = SourceSubCategories.ensure(source.category_name, source.subcategory_name)
            if not  subcategory:
                AppLogging.error("Source:{} Cannot create category with name {} subcategory name {}".format(source.id, source.category_name, source.subcategory_name))
                source.save()
                continue

            source.category = category
            source.subcategory = subcategory

            source.save()

    def get_favicon(self):
        return self.favicon

    def save(self, *args, **kwargs):
        SourceSubCategories.cleanup()
        SourceCategories.cleanup()

        self.category = SourceCategories.ensure(self.category_name)
        self.subcategory = SourceSubCategories.ensure(
            self.category_name, self.subcategory_name
        )

        super().save(*args, **kwargs)

    def get_export_names():
        return [
            "id",
            "url",
            "title",
            "category_name",
            "subcategory_name",
            "export_to_cms",
            "remove_after_days",
            "language",
            "age",
            "favicon",
            "enabled",
            "fetch_period",
            "source_type",
            "proxy_location",
        ]

    def get_all_export_names():
        """
        Provides object export names with dependencies from other objects
        """
        names = set(BaseLinkDataController.get_export_names())
        names.add("category__category_id")
        names.add("subcategory__subcategory_id")
        return list(names)

    def get_query_names():
        return sorted(
            [
                "id",
                "url",
                "title",
                "category_name",
                "subcategory_name",
                "export_to_cms",
                "remove_after_days",
                "language",
                "age",
                "favicon",
                "enabled",
                "fetch_period",
                "source_type",
                "proxy_location",
                "category__category_id",
                "subcategory__subcategory_id",
                "category__category_name",
                "subcategory__subcategory_name",
            ]
        )


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
