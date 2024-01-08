from pathlib import Path
import shutil

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import ConfigurationEntry
from ..controllers import LinkDataController, DomainsController
from .utilities import WebPageDisabled


class DomainTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_domain_add(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

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

    def test_domain_create_missing_entries(self):
        LinkDataController.objects.all().delete()
        DomainsController.objects.all().delete()

        DomainsController.objects.create(domain = "waiterrant.blogspot.com")

        DomainsController.create_missing_entries()

        self.assertEqual(LinkDataController.objects.all().count(), 1)
