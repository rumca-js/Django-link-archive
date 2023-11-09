import os
from datetime import datetime, date

from django.db import models
from django.urls import reverse
import django.utils

from ..apps import LinkDatabase
from ..webtools import Page, RssPropertyReader
from .entries import LinkDataModel


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

    link_obj = models.OneToOneField(
        LinkDataModel,
        on_delete=models.SET_NULL,
        related_name="domain_obj",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "-link_obj__page_rating",
            "-category",
            "-subcategory",
            "tld",
            "suffix",
            "main",
            "domain",
        ]

    def add(url):
        """
        Public API
        """
        wh = url.find(":")
        if wh > 8:
            url = url[:wh]

        if url.strip() == "":
            print("Provided invalid URL, empty")
            return

        if url.find("http") == -1:
            url = "https://" + url

        domain_text = Domains.get_domain_url(url)
        if (
            not domain_text
            or domain_text == ""
            or domain_text == "https://"
            or domain_text == "http://"
        ):
            print("Not domain text")

        return Domains.create_or_update_domain(domain_text)

    def get_domain_url(input_url):
        from ..webtools import Page

        p = Page(input_url)
        domain_text = p.get_domain_only()
        return domain_text

    def get_domain_full_url(self, protocol=None):
        if protocol is None:
            return self.protocol + "://" + self.domain
        else:
            return protocol + "://" + self.domain

    def get_absolute_url(self):
        return reverse(
            "{}:domain-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

    def create_or_update_domain(domain_only_text):
        print("Creating, or updating domain {}".format(domain_only_text))
        objs = Domains.objects.filter(domain=domain_only_text)

        if objs.count() == 0:
            props = Domains.get_link_properties(domain_only_text)
            obj = Domains.create_object(domain_only_text, props)
        else:
            obj = objs[0]
        #    Domains.update_object(obj)

        if obj:
            return obj.id

    def create_object(domain_only_text, props):
        import tldextract

        if props:
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

            ob.update_complementary_data(True)
            ob.add_domain_link(props)
            ob.check_and_create_source(props)

            return ob

    def get_link_properties(domain_only):
        http_position = domain_only.find("http")
        if http_position == 0:
            domain_only = domain_only[http_position + 7 :]

        link = "https://" + domain_only

        p = Page(link)
        if p.get_contents() is None:
            link = "http://" + domain_only
            p = Page(link)
            if p.get_contents() is None:
                return
            return p.get_properties_map()

        return p.get_properties_map()

    def get_page_properties(self):
        # if self.link_obj is not None:
        #    return

        link = Domains.get_domain_url(self.get_domain_full_url())
        return Domains.get_link_properties(link)

    def update_object(self, force=False):
        if self.is_domain_set() == False:
            self.update_domain()

        self.update_complementary_data(force)

        if self.link_obj == None:
            props = self.get_page_properties()
            if props:
                self.add_domain_link(props)
                self.check_and_create_source(props)
            else:
                self.dead = True
                self.save()

    def add_domain_link(self, props):
        from ..controllers import LinkDataHyperController

        entry = LinkDataHyperController.get_link_object(props["link"])
        if entry:
            if self.link_obj == None:
                self.link_obj = entry
                self.save()
                entry.permanent = True
                entry.save()
            return entry

        link_props = {}
        link_props["link"] = props["link"]
        link_props["title"] = props["title"]
        link_props["description"] = props["description"]
        link_props["page_rating_contents"] = props["page_rating"]
        link_props["page_rating"] = props["page_rating"]
        link_props["language"] = props["language"]

        entry = LinkDataHyperController.add_new_link(link_props)
        entry.permanent = True
        entry.save()

        self.link_obj = entry
        self.save()

        return entry

    def check_and_create_source(self, props):
        from ..webtools import Page
        from .sources import SourceDataModel
        from ..configuration import Configuration
        from .admin import PersistentInfo

        rss_url = props["rss_url"]
        if not rss_url:
            return

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        if SourceDataModel.objects.filter(url=rss_url).count() > 0:
            return

        if self.link_obj and self.link_obj.dead:
            return

        conf = Configuration.get_object().config_entry

        if not conf.auto_store_sources:
            return

        parser = RssPropertyReader(rss_url)
        d = parser.parse()
        if d is None:
            PersistentInfo.error("RSS is empty: rss_url:{0}".format(rss_url))
            return

        if len(d.entries) == 0:
            PersistentInfo.error("RSS no entries: rss_url:{0}".format(rss_url))
            return

        props = {}
        props["url"] = rss_url

        if "title" in d.feed:
            props["title"] = d.feed.title
        props["export_to_cms"] = False
        if "language" in d.feed:
            props["language"] = d.feed.language
        if "image" in d.feed:
            if "href" in d.feed.image:
                props["favicon"] = d.feed.image["href"]
            else:
                props["favicon"] = d.feed.image
        props["on_hold"] = not conf.auto_store_sources_enabled
        props["source_type"] = SourceDataModel.SOURCE_TYPE_RSS
        props["remove_after_days"] = 2
        props["category"] = "New"
        props["subcategory"] = "New"

        try:
            SourceDataModel.objects.create(**props)
        except Exception as E:
            pass

    def update_complementary_data(self, force=False):
        DomainsSuffixes.add(self.suffix)
        DomainsTlds.add(self.tld)
        DomainsMains.add(self.main)

        # if self.is_update_time() or force:
        #    self.update_page_info()

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

        days = DateUtils.get_day_diff(self.date_update_last)
        # TODO make this configurable
        return days > Domains.get_update_days_limit()

    def get_update_days_limit():
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

            self.update_complementary_data()

        else:
            print("domain:{} Nothing has changed".format(self.domain))

    def update_page_info(self):
        # if self.title is not None and self.description is not None and self.dead == False and not force:
        #    print("Domain: not fixing title/description {} {} {}".format(self.domain, self.suffix, self.tld))
        #    return False
        if self.link_obj is not None:
            return

        print("Fixing title {}".format(self.domain))

        from ..dateutils import DateUtils
        from ..webtools import Page

        date_before_limit = DateUtils.get_days_before_dt(
            Domains.get_update_days_limit()
        )
        if self.date_update_last >= date_before_limit:
            return

        changed = False

        p = Page(self.get_domain_full_url())

        new_title = p.get_title()
        new_description = p.get_description_safe()[:998]
        new_language = p.get_language()
        protocol = self.protocol

        if new_title is None:
            print("{} Trying with http".format(self.domain))
            p = Page(self.get_domain_full_url("http"))
            new_title = p.get_title()
            new_description = p.get_description_safe()[:998]
            new_language = p.get_language()

        print("Page status:{}".format(p.is_status_ok()))

        self.status_code = p.status_code

        is_title_invalid = new_title and (
            new_title.find("Forbidden") >= 0 or new_title.find("Access denied") >= 0
        )

        if p.is_status_ok() == False or is_title_invalid:
            self.dead = True

            self.date_update_last = DateUtils.get_datetime_now_utc()

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
            self.date_update_last = DateUtils.get_datetime_now_utc()

            self.protocol = protocol
            self.save()

    def update_all(domains=None):
        if domains is None:
            from ..dateutils import DateUtils

            date_before_limit = DateUtils.get_days_before_dt(
                Domains.get_update_days_limit()
            )

            domains = Domains.objects.filter(
                date_update_last__lt=date_before_limit, dead=False, link_obj=None
            )
            # domains = Domains.objects.filter(dead = True) #, description__isnull = True)

        for domain in domains:
            print("Fixing:{}".format(domain.domain))
            try:
                domain.update_object()
            except Exception as e:
                print(str(e))
            print("Fixing:{} done".format(domain.domain))

    def remove_all():
        domains = Domains.objects.all()
        domains.delete()

        suffs = DomainsSuffixes.objects.all()
        suffs.delete()

        tlds = DomainsTlds.objects.all()
        tlds.delete()

        mains = DomainsMains.objects.all()
        mains.delete()

    def remove(self):
        from ..controllers import LinkDataHyperController

        link = self.get_domain_full_url()
        entry = LinkDataHyperController.get_link_object(link)
        if entry:
            entry.delete()

        self.delete()

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
            "date_update_last": self.date_update_last.isoformat(),
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
            "date_update_last",
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

        if category and category != "" and subcategory and subcategory != "":
            objs = DomainSubCategories.objects.filter(
                category=category, subcategory=subcategory
            )
            if objs.count() == 0:
                DomainSubCategories.objects.create(
                    category=category,
                    subcategory=subcategory,
                    category_obj=category_obj,
                )
