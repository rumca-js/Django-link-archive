from django.db import models
from django.urls import reverse
import django.utils
import traceback

from webtoolkit import UrlLocation


class Domains(models.Model):
    """
    Domains should be thought of something additional toward entries.
    For example:
      if there is not entry, then this object definitely should be removed
    """

    domain = models.CharField(max_length=1000, unique=True)
    main = models.CharField(max_length=200, null=True)
    subdomain = models.CharField(max_length=200, null=True)
    suffix = models.CharField(max_length=20, null=True)
    tld = models.CharField(max_length=20, null=True)

    # entry = models.ForeignKey(
    #   LinkDataModel,
    #   on_delete=models.CASCADE,
    #   related_name="domain",
    #   null=True,
    #   blank=True,
    # )

    class Meta:
        ordering = [
            # "-link_obj__page_rating",
            "tld",
            "suffix",
            "main",
            "domain",
        ]

    def remove_all():
        BATCH_SIZE = 1000
        domains = Domains.objects.all()
        domains.delete()
        # while domains.exists():
        #    domains[:BATCH_SIZE].delete()

        suffs = DomainsSuffixes.objects.all()
        suffs.delete()
        # while suffs.exists():
        #    suffs[:BATCH_SIZE].delete()

        tlds = DomainsTlds.objects.all()
        tlds.delete()
        # while tlds.exists():
        #    tlds[:BATCH_SIZE].delete()

        mains = DomainsMains.objects.all()
        mains.delete()
        # while mains.exists():
        #    mains[:BATCH_SIZE].delete()

    def update_complementary_data(self, force=False):
        DomainsSuffixes.add(self.suffix)
        DomainsTlds.add(self.tld)
        DomainsMains.add(self.main)

    def update(self, entry):
        p = UrlLocation(entry.link)
        if p.is_domain():
            domain_only = p.get_domain_only()

            if self.domain != domain_only:
                domains = Domains.objects.filter(domain=domain_only)
                if domains.exists():
                    domains.delete()

            self.domain = domain_only
            self.save()


class DomainsSuffixes(models.Model):
    suffix = models.CharField(max_length=20, null=True, unique=True)

    def add(suffix):
        suffixes = DomainsSuffixes.objects.filter(suffix=suffix)
        if not suffixes.exists():
            DomainsSuffixes.objects.create(suffix=suffix)


class DomainsTlds(models.Model):
    tld = models.CharField(max_length=20, null=True, unique=True)

    def add(tld):
        tlds = DomainsTlds.objects.filter(tld=tld)
        if not tlds.count():
            DomainsTlds.objects.create(tld=tld)


class DomainsMains(models.Model):
    main = models.CharField(max_length=200, null=True, unique=True)

    def add(main):
        mains = DomainsMains.objects.filter(main=main)
        if not mains.exists():
            DomainsMains.objects.create(main=main)
