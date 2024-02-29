from django.db import models
from django.urls import reverse
import django.utils
import traceback


class Domains(models.Model):
    protocol = models.CharField(
        max_length=100, default="https"
    )  # http or https, or ssl
    domain = models.CharField(max_length=1000, unique=True)
    main = models.CharField(max_length=200, null=True)
    subdomain = models.CharField(max_length=200, null=True)
    suffix = models.CharField(max_length=20, null=True)
    tld = models.CharField(max_length=20, null=True)
    category = models.CharField(max_length=1000, null=True)
    subcategory = models.CharField(max_length=1000, null=True)
    dead = models.BooleanField(default=False)  # to be removed

    date_created = models.DateTimeField(auto_now_add=True)
    date_update_last = models.DateTimeField(auto_now=True)  # to be removed

    # link_obj = models.OneToOneField(
    #    LinkDataModel,
    #    on_delete=models.SET_NULL,
    #    related_name="main_domain_obj",
    #    null=True,
    #    blank=True,
    # )

    class Meta:
        ordering = [
            # "-link_obj__page_rating",
            "-category",
            "-subcategory",
            "tld",
            "suffix",
            "main",
            "domain",
        ]

    def remove_all():
        domains = Domains.objects.all()
        domains.delete()

        suffs = DomainsSuffixes.objects.all()
        suffs.delete()

        tlds = DomainsTlds.objects.all()
        tlds.delete()

        mains = DomainsMains.objects.all()
        mains.delete()

    def update_complementary_data(self, force=False):
        DomainsSuffixes.add(self.suffix)
        DomainsTlds.add(self.tld)
        DomainsMains.add(self.main)

        # if self.is_update_time() or force:
        #    self.update_page_info()

    def get_update_days_limit():
        return 7


class DomainsSuffixes(models.Model):
    suffix = models.CharField(max_length=20, null=True, unique=True)

    def add(suffix):
        suffixes = DomainsSuffixes.objects.filter(suffix=suffix)
        if suffixes.count() == 0:
            DomainsSuffixes.objects.create(suffix=suffix)


class DomainsTlds(models.Model):
    tld = models.CharField(max_length=20, null=True, unique=True)

    def add(tld):
        tlds = DomainsTlds.objects.filter(tld=tld)
        if tlds.count() == 0:
            DomainsTlds.objects.create(tld=tld)


class DomainsMains(models.Model):
    main = models.CharField(max_length=200, null=True, unique=True)

    def add(main):
        mains = DomainsMains.objects.filter(main=main)
        if mains.count() == 0:
            DomainsMains.objects.create(main=main)


class DomainCategories(models.Model):
    category = models.CharField(max_length=1000, unique=True)

    class Meta:
        ordering = ["category"]

    def add(category):
        if category and category != "":
            objs = DomainCategories.objects.filter(category=category)
            if objs.count() == 0:
                return DomainCategories.objects.create(category=category)
            else:
                return objs[0]


class DomainSubCategories(models.Model):
    category = models.CharField(max_length=1000, default="")
    subcategory = models.CharField(max_length=1000)

    category_obj = models.ForeignKey(
        DomainCategories,
        on_delete=models.SET_NULL,
        related_name="subcategories",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["category", "subcategory"]

    def add(category, subcategory):
        category_obj = None
        category_objs = DomainCategories.objects.filter(category=category)
        if category_objs.count() > 0:
            category_obj = category_objs[0]
        else:
            category_obj = DomainCategories.add(category)

        if category and category != "" and subcategory and subcategory != "":
            objs = DomainSubCategories.objects.filter(
                category=category, subcategory=subcategory
            )
            if objs.count() == 0:
                return DomainSubCategories.objects.create(
                    category=category,
                    subcategory=subcategory,
                    category_obj=category_obj,
                )
            else:
                return objs[0]
