import os
from datetime import datetime, date

from django.db import models
from django.urls import reverse
import django.utils

from ..apps import LinkDatabase


class Domains(models.Model):
    protocol = models.CharField(
        max_length=100, default="https"
    )  # http or https, or ssl
    domain = models.CharField(max_length=1000, unique=True)
    main = models.CharField(max_length=200, null=True)
    subdomain = models.CharField(max_length=200, null=True)
    suffix = models.CharField(max_length=20, null=True)
    tld = models.CharField(max_length=20, null=True)
    title = models.CharField(max_length=500, null=True)
    description = models.CharField(max_length=1000, null=True)
    language = models.CharField(max_length=1000, default="en")
    status_code = models.IntegerField(default=200)
    category = models.CharField(max_length=1000, null=True)
    subcategory = models.CharField(max_length=1000, null=True)
    dead = models.BooleanField(default=False)

    date_created = models.DateTimeField(default=django.utils.timezone.now)
    date_last = models.DateTimeField(default=django.utils.timezone.now)

    class Meta:
        ordering = ["tld", "suffix", "main", "domain"]

    def add(url):
        """
        Public API
        """
        wh = url.find(":")
        if wh > 8:
            url = url[:wh]

        domain_text = Domains.get_domain_url(url)
        return Domains.create_or_update_domain(domain_text)

    def get_domain_url(input_url):
        if input_url.find("/") >= 0:
            from ..webtools import Page

            p = Page(input_url)
            domain_text = p.get_domain_only()
            return domain_text
        else:
            return input_url

    def get_absolute_url(self):
        return reverse(
            "{}:domain-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

    def create_or_update_domain(domain_only_text):
        objs = Domains.objects.filter(domain=domain_only_text)
        if objs.count() == 0:
            return Domains.create_object(domain_only_text)
        else:
            Domains.update_object(objs[0])
            return objs[0]

    def create_object(domain_only_text):
        import tldextract

        extract = tldextract.TLDExtract()
        domain_data = extract(domain_only_text)

        tld = os.path.splitext(domain_only_text)[1][1:]

        ob = Domains.objects.create(
            domain=domain_only_text,
            main=domain_data.domain,
            subdomain=domain_data.subdomain,
            suffix=domain_data.suffix,
            tld=tld,
        )

        Domains.update_complementary_data(ob, True)

        return ob

    def update_object(self, force=False):
        if self.is_domain_set() == False:
            self.update_domain()

        self.update_complementary_data(force)

    def update_complementary_data(self, force=False):
        DomainsSuffixes.add(self.suffix)
        DomainsTlds.add(self.tld)
        DomainsMains.add(self.main)

        if self.is_update_time() or force:
            self.update_page_info()

    def get_domain_ext(self, domain_only_text):
        tld = os.path.splitext(domain_only_text)[1][1:]
        wh = tld.find(":")
        if wh >= 0:
            tld = tld[:wh]
        return tld

    def is_domain_set(self):
        return (
            self.suffix is not None
            and self.tld is not None
            and self.suffix != ""
            and self.tld != ""
        )

    def is_page_info_set(self):
        return (
            self.title is not None
            and self.description is not None
            and self.language is not None
        )

    def is_update_time(self):
        from ..dateutils import DateUtils

        days = DateUtils.get_day_diff(self.date_last)
        # TODO make this configurable
        return days > self.get_update_days_limit()

    def get_update_days_limit(self):
        return 7

    def update_domain(self):
        import tldextract
        from ..dateutils import DateUtils

        changed = False

        if self.suffix is None or self.suffix == "":
            extract = tldextract.TLDExtract()
            domain_data = extract(self.domain)

            self.main = domain_data.domain
            self.subdomain = domain_data.subdomain
            self.suffix = domain_data.suffix
            changed = True

        if self.tld is None or self.tld == "":
            self.tld = self.get_domain_ext(self.domain)
            changed = True

        if changed:
            print(
                "domain:{} subdomain:{} suffix:{} tld:{} title:{}".format(
                    self.main, self.subdomain, self.suffix, self.tld, self.title
                )
            )

            self.save()

            Domains.update_complementary_data(self)

        else:
            print("domain:{} Nothing has changed".format(self.domain))

    def update_page_info(self):
        # if self.title is not None and self.description is not None and self.dead == False and not force:
        #    print("Domain: not fixing title/description {} {} {}".format(self.domain, self.suffix, self.tld))
        #    return False
        print("Fixing title {}".format(self.domain))

        changed = False

        from ..webtools import Page

        p = Page(self.protocol + "://" + self.domain)

        new_title = p.get_title()
        new_description = p.get_description()
        new_language = p.get_language()
        protocol = self.protocol

        if new_title is None:
            print("{} Trying with http".format(self.domain))
            protocol = "http"
            p = Page(protocol + "://" + self.domain)
            new_title = p.get_title()
            new_description = p.get_description()
            new_language = p.get_language()

        print("Page status:{}".format(p.is_status_ok()))

        self.status_code = p.status_code

        is_title_invalid = new_title and (
            new_title.find("Forbidden") >= 0 or new_title.find("Access denied") >= 0
        )

        if p.is_status_ok() == False or is_title_invalid:
            self.dead = True

            from ..dateutils import DateUtils

            self.date_last = DateUtils.get_datetime_now_utc()

            self.save()
            return
        if self.dead and p.is_status_ok():
            self.dead = False
            changed = True

        print("New title:{}".format(new_title))
        print("New description:{}".format(new_description))

        if new_title is not None:
            self.title = new_title
            changed = True
        if new_description is not None:
            self.description = new_description
            changed = True
        if new_language is not None:
            self.language = new_language
            changed = True
        if new_title is not None and new_description is None:
            self.description = None
            changed = True

        if changed:
            from ..dateutils import DateUtils

            self.date_last = DateUtils.get_datetime_now_utc()

            self.protocol = protocol
            self.save()

    def update_all(domains=None):
        if domains is None:
            from ..dateutils import DateUtils

            date_before_limit = DateUtils.get_days_before_dt(
                self.get_update_days_limit()
            )

            domains = Domains.objects.filter(date_last__lt=date_before_limit)
            # domains = Domains.objects.filter(dead = True) #, description__isnull = True)

        for domain in domains:
            print("Fixing:{}".format(domain.domain))
            domain.update_object()

    def remove_all():
        domains = Domains.objects.all()
        domains.delete()

        suffs = DomainsSuffixes.objects.all()
        suffs.delete()

        tlds = DomainsTlds.objects.all()
        tlds.delete()

        mains = DomainsMains.objects.all()
        mains.delete()

    def get_map(self):
        result = {
            "protocol": self.protocol,
            "domain": self.domain,
            "main": self.main,
            "subdomain": self.subdomain,
            "suffix": self.suffix,
            "tld": self.tld,
            "title": self.title,
            "description": self.description,
            "language": self.language,
            "status_code": self.status_code,
            "category": self.category,
            "subcategory": self.subcategory,
            "dead": self.dead,
            "date_created": self.date_created.isoformat(),
            "date_last": self.date_last.isoformat(),
        }
        return result

    def get_query_names():
        result = [
            "protocol",
            "domain",
            "main",
            "subdomain",
            "suffix",
            "tld",
            "title",
            "description",
            "language",
            "status_code",
            "category",
            "subcategory",
            "dead",
            "date_created",
            "date_last",
        ]
        return result

    def reset_dynamic_data():
        objs = DomainCategories.objects.all()
        objs.delete()
        objs = DomainSubCategories.objects.all()
        objs.delete()

        domains = Domains.objects.all()
        for domain in domains:
            DomainCategories.add(domain.category)
            DomainSubCategories.add(domain.category, domain.subcategory)

    def get_description_safe(self):
        if self.description:
            if len(self.description) > 100:
                return self.description[:100] + "..."
            else:
                return self.description
        else:
            return ""


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
    main = models.CharField(max_length=20, null=True, unique=True)

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
                DomainCategories.objects.create(category=category)


class DomainSubCategories(models.Model):
    category = models.CharField(max_length=1000, default="")
    subcategory = models.CharField(max_length=1000)

    class Meta:
        ordering = ["category", "subcategory"]

    def add(category, subcategory):
        if category and category != "" and subcategory and subcategory != "":
            objs = DomainSubCategories.objects.filter(
                category=category, subcategory=subcategory
            )
            if objs.count() == 0:
                DomainSubCategories.objects.create(
                    category=category, subcategory=subcategory
                )
