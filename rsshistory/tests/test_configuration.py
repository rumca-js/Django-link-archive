from ..configuration import Configuration
from ..models import SystemOperation

from .fakeinternet import FakeInternetTestCase


class ConfigurationTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    # def test_encrypt_decrypt(self):
    #    c = Configuration.get_object()

    #    # call tested function
    #    encoded = c.encrypt("text")

    #    self.assertTrue(encoded)

    #    # call tested function
    #    decoded = c.decrypt(encoded)

    #    self.assertTrue(decoded)
    #    self.assertEqual(decoded, "text")

    def test_refresh__refreshprocessor(self):
        SystemOperation.objects.all().delete()

        c = Configuration.get_object()
        c.refresh("RefreshProcessor")

        operations = SystemOperation.objects.all()
        self.assertEqual(operations.count(), 1)
        self.assertEqual(operations[0].is_internet_connection_checked, True)
        self.assertEqual(operations[0].is_internet_connection_ok, True)

    def test_refresh__not_refreshprocessor(self):
        SystemOperation.objects.all().delete()

        c = Configuration.get_object()
        c.refresh("NotRefreshProcessor")

        operations = SystemOperation.objects.all()
        self.assertEqual(operations.count(), 1)
        self.assertEqual(operations[0].is_internet_connection_checked, False)
