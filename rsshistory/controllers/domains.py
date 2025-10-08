from datetime import datetime, date, timedelta
import os
import traceback

from django.db import models
from django.urls import reverse
from django.db.models import Q

from webtoolkit import UrlLocation
from utils.dateutils import DateUtils

from ..models import (
    AppLogging,
    Domains,
    DomainsTlds,
    DomainsSuffixes,
    DomainsMains,
    ConfigurationEntry,
)
from .entries import LinkDataController
from ..configuration import Configuration
from ..apps import LinkDatabase


class DomainsController(Domains):
    """ """

    class Meta:
        proxy = True

    def get_map(self):
        result = {
            "domain": self.domain,
            "main": self.main,
            "subdomain": self.subdomain,
            "suffix": self.suffix,
            "tld": self.tld,
        }
        return result

    def get_query_names():
        result = [
            "domain",
            "main",
            "subdomain",
            "suffix",
            "tld",
        ]
        return result

    def add(url):
        """
        Public API
        @return domain object
        """
        conf = Configuration.get_object().config_entry
        if not conf.enable_domain_support:
            return
        if not conf.accept_domain_links:
            return

        protocol = UrlLocation(url).get_scheme()

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

        return DomainsController.create_object(domain_text, protocol)

    def cleanup(cfg=None):
        conf = Configuration.get_object().config_entry
        if conf.enable_domain_support:
            DomainsController.check_consistency_all(cfg)
        else:
            DomainsController.remove_all()

    def truncate(cfg=None):
        DomainsController.remove_all()

    def get_link_object(self):
        if not hasattr(self, "link_obj"):
            entries = LinkDataController.objects.filter(link=self.get_domain_full_url())
            if len(entries) > 0:
                self.link_obj = entries[0]
                return self.link_obj
        else:
            return self.link_obj

    def check_consistency_all(cfg=None):
        if cfg is not None and "verify" in cfg:
            for domain in DomainsController.objects.all():
                if not domain.check_consistency():
                    domain.delete()

        DomainsController.create_missing_domains()

    def check_consistency(self):
        if self.check_local_consistency():
            return True

        return False

    def check_local_consistency(self):
        entries = LinkDataController.objects.filter(link="https://" + self.domain)
        if entries.exists():
            entry = entries[0]
            entry.domain = self
            entry.save()
            return True

        entries = LinkDataController.objects.filter(link="http://" + self.domain)
        if entries.exists():
            entry = entries[0]
            entry.domain = self
            entry.save()
            return True

        entries = LinkDataController.objects.filter(link="smb://" + self.domain)
        if entries.exists():
            entry = entries[0]
            entry.domain = self
            entry.save()
            return True

        entries = LinkDataController.objects.filter(link="ftp://" + self.domain)
        if entries.exists():
            entry = entries[0]
            entry.domain = self
            entry.save()
            return True

        entries = LinkDataController.objects.filter(link="//" + self.domain)
        if entries.exists():
            entry = entries[0]
            entry.domain = self
            entry.save()
            return True

        return False

    def check_web_consistency(self):
        from .entriesutils import EntryDataBuilder

        full_domain = self.get_domain_full_url("https")

        b = EntryDataBuilder()
        b.link = full_domain
        obj = b.build_from_link()
        if obj:
            return True

        full_domain_http = domain.get_domain_full_url("http")

        b.link = full_domain_http
        obj = b.build_from_link()
        if obj:
            return True

    def create_object(domain_only_text, protocol):
        old_entries = Domains.objects.filter(domain=domain_only_text)
        if old_entries.exists():
            ob = old_entries[0]
        else:
            import tldextract

            extract = tldextract.TLDExtract()
            domain_data = extract(domain_only_text)

            tld = os.path.splitext(domain_only_text)[1][1:]

            ob = DomainsController.objects.create(
                domain=domain_only_text,
                main=domain_data.domain,
                subdomain=domain_data.subdomain,
                suffix=domain_data.suffix,
                tld=tld,
            )

        ob.update_complementary_data(True)

        return ob

    def get_domain_only(input_url):
        p = UrlLocation(input_url)
        domain_text = p.get_domain_only()
        return domain_text

    def get_domain_full_url(self, protocol=None):
        if protocol:
            return protocol + "://" + self.domain
        else:
            return "https://" + self.domain

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

    def remove_unused_domains():
        domains = DomainsController.objects.filter(
            Q(entry_objects__isnull=True) & Q(archive_entry_objects__isnull=True)
        )
        domains.delete()

    def create_missing_domains():
        if not Configuration.get_object().config_entry.accept_domain_links:
            return

        entries = LinkDataController.objects.filter(domain__isnull=True)
        for entry in entries:
            p = UrlLocation(entry.link)
            domain_url = p.get_domain()
            domain_only = p.get_domain_only()

            LinkDatabase.info(
                "Entry:{} domain:{} {}".format(entry.link, domain_url, domain_only)
            )

            domains = DomainsController.objects.filter(domain=domain_only)
            if not domains.exists():
                LinkDatabase.info(
                    "Create missing domains entry:{} - missing domain".format(
                        entry.link
                    )
                )
                domain = DomainsController.add(domain_url)
                entry.domain = domain
                entry.save()
            else:
                LinkDatabase.info(
                    "Create missing domains entry:{} - missing domain link".format(
                        entry.link
                    )
                )
                entry.domain = domains[0]
                entry.save()
