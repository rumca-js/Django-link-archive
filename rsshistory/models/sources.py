from django.db import models
from django.urls import reverse

from ..webtools import DomainAwarePage

from ..apps import LinkDatabase


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
            if objs.count() == 0:
                return SourceCategories.objects.create(name=category_name)

    def get(category_name):
        objs = SourceCategories.objects.filter(name=category_name)
        if objs.count() != 0:
            return objs[0]



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
        if category_name and category_name != "" and subcategory_name and subcategory_name != "":

            category = SourceCategories.ensure(category_name)
            if not category:
                return

            objs = SourceSubCategories.objects.filter(
                category_name=category_name, name=subcategory_name
            )
            if objs.count() == 0:
                return SourceSubCategories.objects.create(
                    category_name=category_name, name=subcategory_name, category = category
                )

    def get(category_name, subcategory_name):
        objs = SourceSubCategories.objects.filter(
            category_name=category_name, name=subcategory_name
        )
        if objs.count() != 0:
            return objs[0]


class SourceDataModel(models.Model):
    SOURCE_TYPE_RSS = "BaseRssPlugin"
    SOURCE_TYPE_JSON = "BaseSourceJsonPlugin"
    SOURCE_TYPE_PARSE = "BaseParsePlugin"
    SOURCE_TYPE_YOUTUBE = "YouTubeChannelPlugin"

    url = models.CharField(max_length=2000, unique=True)
    title = models.CharField(max_length=1000)
    enabled = models.BooleanField(default=True)
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
            SourceCategories.add(source.category_name)
            SourceSubCategories.add(source.category_name, source.subcategory_name)

    def get_favicon(self):
        if self.favicon:
            return self.favicon

        # returning real favicon from HTML is too long

        return DomainAwarePage(self.url).get_domain() + "/favicon.ico"

    def save(self, *args, **kwargs):
        self.category = SourceCategories.ensure(self.category_name)
        self.subcategory = SourceSubCategories.ensure(self.category_name, self.subcategory_name)
        super().save(*args, **kwargs)


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
