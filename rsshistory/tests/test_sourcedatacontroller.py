from ..models import SourceCategories, SourceSubCategories

from ..controllers import (
    SourceDataController,
    SourceDataBuilder,
    BackgroundJobController,
)

from .fakeinternet import FakeInternetTestCase


class SourceDataControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        SourceDataController.objects.all().delete()

    def test_cleanup(self):
        ob = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        SourceCategories.objects.create(name="test1")
        SourceSubCategories.objects.create(category_name="test1", name="test2")

        # nothing is connected. Stray categories are removed

        # call tested function
        SourceDataController.cleanup()

        self.assertEqual(SourceCategories.objects.all().count(), 0)
        self.assertEqual(SourceSubCategories.objects.all().count(), 0)
