from utils.dateutils import DateUtils
from ..webtools import calculate_hash

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
from ..pluginurl import UrlHandlerEx

from .fakeinternet import FakeInternetTestCase


class SourceDataControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

        SourceDataController.objects.all().delete()

    def test_cleanup(self):
        source = SourceDataController.objects.create(
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
        oate_fetched = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")

        source = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        date_fetched = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        ahash = calculate_hash("test")

        source.set_operational_info(date_fetched, 20, 3, ahash, valid=False)

        operations = SourceOperationalData.objects.all()
        self.assertEqual(operations.count(), 1)

        operation = operations[0]
        self.assertEqual(operation.consecutive_errors, 1)

    def test_set_operational_info__max_errors(self):
        SourceOperationalData.objects.all().delete()

        source = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        SourceOperationalData.objects.create(source_obj = source, consecutive_errors = 30)

        date_fetched = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        ahash = calculate_hash("test")

        source.set_operational_info(date_fetched, 20, 3, ahash, valid=False)

        operations = SourceOperationalData.objects.all()
        self.assertEqual(operations.count(), 1)

        operation = operations[0]
        self.assertEqual(operation.consecutive_errors, 31)

        sources = SourceDataController.objects.all()
        self.assertEqual(sources.count(), 1)
        source = sources[0]
        self.assertFalse(source.enabled)

    def test_disable_enable(self):
        source = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
        )

        self.assertTrue(source.enabled)

        # call tested function
        source.disable()

        self.assertFalse(source.enabled)

        # call tested function
        source.enable()

        self.assertTrue(source.enabled)

    def test_update_data(self):
        source = SourceDataController.objects.create(
            url="https://www.codeproject.com/WebServices/NewsRSS.aspx",
            title="YouTube",
            favicon="https://www.codeproject.com/favicon.ico",
        )

        new_favicon = "https://www.codeproject.com/App_Themes/Std/Img/logo100x30.gif"

        rss = UrlHandlerEx("https://www.codeproject.com/WebServices/NewsRSS.aspx")

        # call tested function
        source.update_data(update_with = rss)

        self.assertEqual(source.favicon, new_favicon)
