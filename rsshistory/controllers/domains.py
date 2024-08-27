from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from webtools import DomainAwarePage
from utils.dateutils import DateUtils

from ..models import (
    AppLogging,
    Domains,
    DomainsTlds,
    DomainsSuffixes,
    DomainsMains,
)
from .entries import LinkDataController
from ..configuration import Configuration
from ..apps import LinkDatabase


class DomainsController(Domains):
    """ """

    class Meta:
        proxy = True

    def add(url):
        """
        Public API
        """
        if not Configuration.get_object().config_entry.accept_domains:
            return

        protocol = DomainAwarePage(url).get_scheme()

        domain_text = DomainsController.get_domain_only(url)
        if (
            not domain_text
            or domain_text == ""
            or domain_text == "https://"
            or domain_text == "http://"
            or domain_text == "https"
            or domain_text == "http"
        ):
            AppLogging.error("Not a domain text:{}, url:{}".format(domain_text, url))
            return

        return DomainsController.create_or_update_domain(domain_text, protocol)

    def create_or_update_domain(domain_only_text, protocol):
        LinkDatabase.info("Creating, or updating domain:{}".format(domain_only_text))
        objs = Domains.objects.filter(domain=domain_only_text)

        obj = None
        if objs.count() == 0:
            try:
                obj = DomainsController.create_object(domain_only_text, protocol)
            except Exception as E:
                exc_str = traceback.format_exc()
                AppLogging.exc(
                    E,
                    "Cannot create domain data:{}\n{}".format(
                        domain_only_text, exc_str
                    ),
                )
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

    def create_object(domain_only_text, protocol):
        import tldextract

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
            ob.protocol = protocol
            ob.save()

        else:
            ob = DomainsController.objects.create(
                domain=domain_only_text,
                main=domain_data.domain,
                subdomain=domain_data.subdomain,
                suffix=domain_data.suffix,
                tld=tld,
                protocol=protocol,
            )

            ob.update_complementary_data(True)

        return ob

    def get_domain_only(input_url):
        p = DomainAwarePage(input_url)
        domain_text = p.get_domain_only()
        return domain_text

    def get_domain_full_url(self, protocol=None):
        if protocol:
            return protocol + "://" + self.domain
        else:
            return self.protocol + "://" + self.domain

    def get_absolute_url(self):
        return reverse(
            "{}:domain-detail".format(LinkDatabase.name), args=[str(self.id)]
        )

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

    def is_update_time(self):

        days = DateUtils.get_day_diff(self.date_update_last)
        # TODO make this configurable
        return days > Domains.get_update_days_limit()

    def update_domain(self):
        import tldextract

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

    def get_map(self):
        result = {
            "protocol": self.protocol,
            "domain": self.domain,
            "main": self.main,
            "subdomain": self.subdomain,
            "suffix": self.suffix,
            "tld": self.tld,
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
            "dead",
            "date_created",
            "date_update_last",
        ]
        return result

    def reset_dynamic_data():
        pass

    def is_domain_object(entry):
        if not hasattr(entry, "main_domain_obj"):
            return False

        return entry.main_domain_obj

    def cleanup():
        if not Configuration.get_object().config_entry.accept_domains:
            DomainsController.unconnect_entries()
            DomainsController.remove_all()
        else:
            DomainsController.remove_unused_domains()

        tlds = DomainsTlds.objects.filter(tld__icontains=":")
        tlds.delete()

        suffixes = DomainsSuffixes.objects.filter(suffix__icontains=":")
        suffixes.delete()

        mains = DomainsMains.objects.filter(main__icontains=":")
        mains.delete()

    def remove_unused_domains():
        domains = DomainsController.objects.filter(
            Q(entry_objects__isnull=True) & Q(archive_entry_objects__isnull=True)
        )
        domains.delete()

    def unconnect_entries():
        entries = LinkDataController.objects.filter(domain_obj__isnull=False)
        for entry in entries:
            entry.domain_obj = None
            entry.save()

    def create_missing_domains():
        if not Configuration.get_object().config_entry.accept_domains:
            return

        entries = LinkDataController.objects.filter(domain_obj__isnull=True)
        for entry in entries:
            p = DomainAwarePage(entry.link)
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

    def create_missing_entries():
        from .entriesutils import EntryDataBuilder

        domains = DomainsController.objects.all()
        for domain in domains:
            missing_entry = False

            full_domain = domain.get_domain_full_url()
            full_domain_http = domain.get_domain_full_url("http")

            entries = LinkDataController.objects.filter(link=full_domain)

            if entries.count() == 0:
                http_entries = LinkDataController.objects.filter(link=full_domain_http)
                if http_entries.count() == 0:
                    missing_entry = True

            if missing_entry:
                b = EntryDataBuilder()
                b.link = full_domain
                obj = b.add_from_link()
                if obj:
                    domain.protocol = "https"
                    domain.save()
                else:
                    b.link = full_domain_http
                    obj = b.add_from_link()
                    if obj:
                        domain.protocol = "http"
                        domain.save()
