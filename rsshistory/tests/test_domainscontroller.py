from ..models import ConfigurationEntry
from ..controllers import LinkDataController, DomainsController
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase


class DomainTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        config = Configuration.get_object().config_entry
        config.accept_domains = True
        config.keep_domains = True
        config.save()
        Configuration.get_object().config_entry = config

    def test_domain_add(self):

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        # call tested function
        DomainsController.add("waiterrant.blogspot.com")

        objs = DomainsController.objects.filter(domain__icontains="waiterrant")

        self.assertEqual(objs.count(), 1)

        obj = objs[0]

        self.assertEqual(obj.domain, "waiterrant.blogspot.com")
        self.assertEqual(obj.main, "blogspot")
        self.assertEqual(obj.subdomain, "waiterrant")
        self.assertEqual(obj.suffix, "com")

        entries = LinkDataController.objects.all()
        self.assertEqual(entries.count(), 0)

    def test_domain_add_https(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        # call tested function
        DomainsController.add("https://waiterrant.blogspot.com")

        objs = DomainsController.objects.filter(domain__icontains="waiterrant")

        self.assertEqual(objs.count(), 1)

        obj = objs[0]

        self.assertEqual(obj.domain, "waiterrant.blogspot.com")
        self.assertEqual(obj.main, "blogspot")
        self.assertEqual(obj.subdomain, "waiterrant")
        self.assertEqual(obj.suffix, "com")

        entries = LinkDataController.objects.all()
        self.assertEqual(entries.count(), 0)

    def test_domain_add_full_link(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        # call tested function
        DomainsController.add("https://waiterrant.blogspot.com/nothing-important")

        objs = DomainsController.objects.filter(domain__icontains="waiterrant")

        self.assertEqual(objs.count(), 1)

        obj = objs[0]

        self.assertEqual(obj.domain, "waiterrant.blogspot.com")
        self.assertEqual(obj.main, "blogspot")
        self.assertEqual(obj.subdomain, "waiterrant")
        self.assertEqual(obj.suffix, "com")

        entries = LinkDataController.objects.all()
        self.assertEqual(entries.count(), 0)

    def test_cleanup__not(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        LinkDataController.objects.create(link="https://waiterrant.blogspot.com")

        DomainsController.objects.create(domain="waiterrant.blogspot.com")

        # call tested function
        DomainsController.cleanup({"verify": True})

        domains = DomainsController.objects.all()
        entries = LinkDataController.objects.all()

        self.assertEqual(domains.count(), 1)
        self.assertEqual(entries.count(), 1)
        self.assertEqual(entries[0].domain, domains[0])

    def test_cleanup__not_recreate(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        DomainsController.objects.create(domain="linkedin.com")

        # call tested function
        DomainsController.cleanup({"verify": True})

        domains = DomainsController.objects.all()
        entries = LinkDataController.objects.all()

        self.assertEqual(domains.count(), 0)
        self.assertEqual(entries.count(), 0)

    def test_link_remove_deletes_domain(self):

        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        entry = LinkDataController.objects.create(link="https://test.com")

        # call tested function
        DomainsController.add("test.com")

        entry.delete()

        domains = DomainsController.objects.filter(domain="test.com")
        self.assertEqual(domains.count(), 0)
