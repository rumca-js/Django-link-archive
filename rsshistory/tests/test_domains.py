from pathlib import Path
import shutil

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import Domains


class DomainTest(TestCase):
    def setUp(self):
        pass

    def test_domain_add(self):
        Domains.add("waiterrant.blogspot.com")

        objs = Domains.objects.filter(domain__icontains="waiterrant")

        self.assertEqual(objs.count(), 1)

        obj = objs[0]

        self.assertEqual(obj.domain, "waiterrant.blogspot.com")
        self.assertEqual(obj.main, "blogspot")
        self.assertEqual(obj.subdomain, "waiterrant")
        self.assertEqual(obj.suffix, "com")
