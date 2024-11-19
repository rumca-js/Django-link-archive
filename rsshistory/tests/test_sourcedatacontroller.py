from ..models import (
    SourceCategories,
    SourceSubCategories,
    SourceOperationalData,
)

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

    def test_set_operational_info(self):
        SourceOperationalData.objects.all().delete()

        ob = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        ob.set_operational_info(date_fetched, 20, 3, "binary", valid=False)

        operations = SourceOperationalData.objects.all()
        self.assertEqual(operations.count(), 1)

        operation = operations[0]
        self.assertEqual(operations.consecutive_errors, 1)

    def test_set_operational_info__max_errors(self):
        SourceOperationalData.objects.all().delete()

        source = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        SourceOperationalData.objects.create(source_obj = source, consecutive_errors = 30)

        ob.set_operational_info(date_fetched, 20, 3, "binary", valid=False)

        operations = SourceOperationalData.objects.all()
        self.assertEqual(operations.count(), 1)

        operation = operations[0]
        self.assertEqual(operations.consecutive_errors, 31)

        source.refresh_from_db()

        self.assertFalse(source.enabled)
