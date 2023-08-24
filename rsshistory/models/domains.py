import os
from datetime import datetime, date

from django.db import models
from django.urls import reverse


class Domains(models.Model):
    domain = models.CharField(max_length=1000)
    main = models.CharField(max_length=200, null=True)
    subdomain = models.CharField(max_length=200, null=True)
    suffix = models.CharField(max_length=20, null=True)
    tld = models.CharField(max_length=20, null=True)

    date_created = models.DateTimeField(default=datetime.now)
    date_last = models.DateTimeField(default=datetime.now)

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
        Domains.create_or_update_domain(domain_text)

    def get_domain_url(input_url):
        if input_url.find("/") >= 0:
            from ..webtools import Page

            p = Page(input_url)
            domain_text = p.get_domain_only()
            return domain_text
        else:
            return input_url

    def create_or_update_domain(domain_only_text):
        objs = Domains.objects.filter(domain=domain_only_text)
        if len(objs) == 0:
            Domains.create_domain_object(domain_only_text)
        else:
            Domains.update_domain_obj(objs[0])

    def create_domain_object(domain_only_text):
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

        Domains.update_complementary_data(ob)

    def update_complementary_data(ob):
        DomainsSuffixes.add(ob.suffix)
        DomainsTlds.add(ob.tld)
        DomainsMains.add(ob.main)

    def get_domain_ext(self, domain_only_text):
        tld = os.path.splitext(domain_only_text)[1][1:]
        wh = tld.find(":")
        if wh >= 0:
            tld = tld[:wh]
        return tld

    def update_domain_obj(obj):
        from ..dateutils import DateUtils

        obj.date_last = DateUtils.get_datetime_now_utc()
        obj.save()

    def fix(self):
        import tldextract
        from ..dateutils import DateUtils

        if self.suffix is not None and self.tld is not None and self.suffix != "" and self.tld != "":
            print("Skipping {} {} {}".format(self.domain, self.suffix, self.tld))
            return False

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
            print("domain:{} subdomain:{} suffix:{} tld:{}".format(self.main, self.subdomain, self.suffix, self.tld))

            self.date_last = DateUtils.get_datetime_now_utc()
            self.save()

            Domains.update_complementary_data(self)

        else:
            print("Nothing has changed")

    def fix_all():
        objs = Domains.objects.all()
        for obj in objs:
            obj.fix()

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
        result = {"domain" : self.domain,
                  "main" : self.main,
                  "subdomain" : self.subdomain,
                  "suffix" : self.suffix,
                  "tld" : self.tld,
                  "date_created" : self.date_created.isoformat(),
                  "date_last" : self.date_last.isoformat(),
                  }
        return result


class DomainsSuffixes(models.Model):
    suffix = models.CharField(max_length=20, null=True, unique=True)

    def add(suffix):
        suffixes = DomainsSuffixes.objects.filter(suffix = suffix)
        if len(suffixes) == 0:
            DomainsSuffixes.objects.create(suffix = suffix)

class DomainsTlds(models.Model):
    tld = models.CharField(max_length=20, null=True, unique=True)

    def add(tld):
        tlds = DomainsTlds.objects.filter(tld = tld)
        if len(tlds) == 0:
            DomainsTlds.objects.create(tld = tld)


class DomainsMains(models.Model):
    main = models.CharField(max_length=20, null=True, unique=True)

    def add(main):
        mains = DomainsMains.objects.filter(main = main)
        if len(mains) == 0:
            DomainsMains.objects.create(main = main)

