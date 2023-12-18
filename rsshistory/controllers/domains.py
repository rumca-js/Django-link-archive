from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from ..models import (
    PersistentInfo,
    Domains,
    DomainCategories,
    DomainSubCategories,
)
from .entries import LinkDataController
from ..configuration import Configuration
from ..webtools import BasePage, HtmlPage
from ..apps import LinkDatabase


class DomainsController(Domains):
    """ """

    class Meta:
        proxy = True

    def add(url):
        """
        Public API
        """
        if not Configuration.get_object().config_entry.auto_store_domain_info:
            return

        domain_text = DomainsController.get_domain_only(url)
        if (
            not domain_text
            or domain_text == ""
            or domain_text == "https://"
            or domain_text == "http://"
            or domain_text == "https"
            or domain_text == "http"
        ):
            PersistentInfo.create(
                "Not a domain text:{}, url:{}".format(domain_text, url)
            )
            return

        return DomainsController.create_or_update_domain(domain_text)

    def create_or_update_domain(domain_only_text):
        LinkDatabase.info("Creating, or updating domain:{}".format(domain_only_text))
        objs = Domains.objects.filter(domain=domain_only_text)

        obj = None
        if objs.count() == 0:
            props = DomainsController.get_link_properties(domain_only_text)
            if props:
                obj = DomainsController.create_object(domain_only_text, props)
        else:
            obj = objs[0]

        return obj

    def get_link_object(self):
        if not hasattr(self, "link_obj"):
            entries = LinkDataController.objects.filter(link=self.get_domain_full_url())
            if len(entries) > 0:
                self.link_obj = entries[0]
                return self.link_obj
        else:
            return self.link_obj

    def create_object(domain_only_text, props):
        import tldextract

        if props:
            extract = tldextract.TLDExtract()
            domain_data = extract(domain_only_text)

            tld = os.path.splitext(domain_only_text)[1][1:]

            old_entries = Domains.objects.filter(domain=domain_only_text)
            if old_entries.count() > 0:
                ob = old_entries[0]
                ob.domain = domain_only_text
                ob.main = domain_data.domain
                ob.subdomain = domain_data.subdomain
                ob.suffix = domain_data.suffix
                ob.tld = tld
                ob.save()

            else:
                ob = DomainsController.objects.create(
                    domain=domain_only_text,
                    main=domain_data.domain,
                    subdomain=domain_data.subdomain,
                    suffix=domain_data.suffix,
                    tld=tld,
                    # link_obj=entry,
                )

                ob.update_complementary_data(True)

            return ob

    def create_missing_domains():
        if not Configuration.get_object().config_entry.auto_store_domain_info:
            return

        entries = LinkDataController.objects.filter(domain_obj=True)
        for entry in entries:
            p = BasePage(entry.link)
            domain_url = p.get_domain()
            domain_only = p.get_domain_only()
            LinkDatabase.info(
                "Entry:{} domain:{} {}".format(entry.link, domain_url, domain_only)
            )

            domains = DomainsController.objects.filter(domain=domain_only)
            if domains.count() == 0:
                LinkDatabase.info(
                    "Create missing domains entry:{} - missing domain".format(
                        entry.link
                    )
                )
                domain = DomainsController.add(domain_url)
                entry.domain_obj = domain
                entry.save()
            else:
                LinkDatabase.info(
                    "Create missing domains entry:{} - missing domain link".format(
                        entry.link
                    )
                )
                entry.domain_obj = domains[0]
                entry.save()

    def get_domain_only(input_url):
        p = BasePage(input_url)
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

    def get_link_properties(domain_only):
        if domain_only.find("http") >= 0:
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            PersistentInfo.create(
                "Cannot obtain properties, expecting only domain:{}\n{}".format(
                    domain_only, line_text
                )
            )
            return

        link = "https://" + domain_only

        p = HtmlPage(link)
        if p.get_contents() is None:
            link = "http://" + domain_only
            p = HtmlPage(link)
            if p.get_contents() is None:
                return
            return p.get_properties()

        return p.get_properties()

    def get_page_properties(self):
        # if self.link_obj is not None:
        #    return

        link = DomainsController.get_domain_only(self.get_domain_full_url())
        return DomainsController.get_link_properties(link)

    def update_object(self, force=False):
        if self.is_domain_set() == False:
            self.update_domain()

        self.update_complementary_data(force)

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
            LinkDatabase.info(
                "domain:{} subdomain:{} suffix:{} tld:{} title:{}".format(
                    self.main, self.subdomain, self.suffix, self.tld, self.title
                )
            )

            self.save()

            self.update_complementary_data()

        else:
            LinkDatabase.info("domain:{} Nothing has changed".format(self.domain))

    def update_page_info(self):
        from ..dateutils import DateUtils

        date_before_limit = DateUtils.get_days_before_dt(
            DomainsController.get_update_days_limit()
        )
        if self.date_update_last >= date_before_limit:
            return

        changed = False

        p = HtmlPage(self.get_domain_full_url())

        new_title = p.get_title()
        new_description = p.get_description_safe()[:998]
        new_language = p.get_language()
        protocol = self.protocol

        if new_title is None:
            p = HtmlPage(self.get_domain_full_url("http"))
            new_title = p.get_title()
            new_description = p.get_description_safe()[:998]
            new_language = p.get_language()

        self.status_code = p.status_code

        if p.is_valid() == False:
            self.dead = True
            self.date_update_last = DateUtils.get_datetime_now_utc()
            self.save()
            return

        if self.dead and p.is_status_ok():
            self.dead = False
            changed = True

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
                date_update_last__lt=date_before_limit, dead=False
            )
            # domains = Domains.objects.filter(dead = True) #, description__isnull = True)

        for domain in domains:
            LinkDatabase.info("Fixing:{}".format(domain.domain))
            try:
                domain.update_object()
            except Exception as e:
                LinkDatabase.info(str(e))
            LinkDatabase.info("Fixing:{} done".format(domain.domain))

    def get_map(self):
        result = {
            "protocol": self.protocol,
            "domain": self.domain,
            "main": self.main,
            "subdomain": self.subdomain,
            "suffix": self.suffix,
            "tld": self.tld,
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

    def is_domain_object(entry):
        if not hasattr(entry, "main_domain_obj"):
            return False

        return entry.main_domain_obj

    def cleanup():
        if not Configuration.get_object().config_entry.auto_store_domain_info:
            Domains.objects.all().delete()

        DomainsController.reset_dynamic_data()
        DomainsController.create_missing_domains()
