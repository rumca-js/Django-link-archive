from datetime import timedelta

from ..models import Gateway
from ..configuration import Configuration
from .fakeinternet import FakeInternetTestCase


class GatewayTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_populate(self):
        # call tested function
        Gateway.populate()

        gateways = Gateway.objects.all()
        self.assertTrue(gateways.count() > 0)

    def test_cleanup__not(self):
        Gateway.objects.all().delete()

        # call tested function
        Gateway.cleanup()

        gateways = Gateway.objects.all()
        self.assertEqual(gateways.count(), 0)

    def test_cleanup__true(self):
        Gateway.objects.all().delete()

        cfg = {}
        cfg["full"] = True

        # call tested function
        Gateway.cleanup(cfg)

        gateways = Gateway.objects.all()
        self.assertTrue(gateways.count() > 0)
