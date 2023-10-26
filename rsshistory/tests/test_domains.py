from pathlib import Path
import shutil

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import Domains, ConfigurationEntry


class DomainTest(TestCase):
    def setUp(self):
        self.disable_web_pages()

    def get_contents_function(self):
        return "test function data"

    def disable_web_pages(self):
        from ..webtools import BasePage, Page

        BasePage.user_agent = None
        BasePage.get_contents_function = self.get_contents_function

        Page.user_agent = None
        entry = ConfigurationEntry.get()
        entry.user_agent = ""
        entry.save()

    def test_domain_add(self):
        Domains.add("waiterrant.blogspot.com")

        objs = Domains.objects.filter(domain__icontains="waiterrant")

        self.assertEqual(objs.count(), 1)

        obj = objs[0]

        self.assertEqual(obj.domain, "waiterrant.blogspot.com")
        self.assertEqual(obj.main, "blogspot")
        self.assertEqual(obj.subdomain, "waiterrant")
        self.assertEqual(obj.suffix, "com")

    def test_domain_add_https(self):
        Domains.add("https://waiterrant.blogspot.com")

        objs = Domains.objects.filter(domain__icontains="waiterrant")

        self.assertEqual(objs.count(), 1)

        obj = objs[0]

        self.assertEqual(obj.domain, "waiterrant.blogspot.com")
        self.assertEqual(obj.main, "blogspot")
        self.assertEqual(obj.subdomain, "waiterrant")
        self.assertEqual(obj.suffix, "com")

    def test_domain_add_full_link(self):
        Domains.add("https://waiterrant.blogspot.com/nothing-important")

        objs = Domains.objects.filter(domain__icontains="waiterrant")

        self.assertEqual(objs.count(), 1)

        obj = objs[0]

        self.assertEqual(obj.domain, "waiterrant.blogspot.com")
        self.assertEqual(obj.main, "blogspot")
        self.assertEqual(obj.subdomain, "waiterrant")
        self.assertEqual(obj.suffix, "com")
