from ..models import ModelFiles
from ..configuration import Configuration
from .fakeinternet import FakeInternetTestCase


class ModelFilesTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        config_entry = Configuration.get_object().config_entry
        config_entry.enable_file_support = True
        config_entry.save()

        Configuration.get_object().config_entry = config_entry

    def test_add(self):
        binary_data = "something".encode()

        ModelFiles.add("https://google.com", binary_data)

        self.assertEqual(ModelFiles.objects.all().count(), 1)
