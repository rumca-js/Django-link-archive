from ..configuration import Configuration

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
