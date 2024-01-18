from ..controllers import (
    SourceDataController,
    SourceDataBuilder,
    BackgroundJobController,
)

from .fakeinternet import FakeInternetTestCase


class SourceControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        source_youtube = SourceDataController.objects.all().delete()

    def test_new_source(self):
        self.assertEqual(SourceDataController.objects.all().count(), 0)

        SourceDataBuilder.add_from_props(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        self.assertEqual(SourceDataController.objects.all().count(), 1)

        # adding a source adds request to fetch data from it
        self.assertEqual(BackgroundJobController.objects.all().count(), 1)

    def test_new_source_twice(self):
        self.assertEqual(SourceDataController.objects.all().count(), 0)

        SourceDataBuilder.add_from_props(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        SourceDataBuilder.add_from_props(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        self.assertEqual(SourceDataController.objects.all().count(), 1)

    def test_source_favicon(self):
        source = SourceDataBuilder.add_from_props(
            {
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        self.assertTrue(source.get_favicon() == "https://linkedin.com/favicon.ico")

    def test_source_get_full_information_page(self):
        url = "https://linkedin.com"

        SourceDataController.objects.all().delete()

        props = SourceDataController.get_full_information({"url": url})

        self.assertTrue(props != None)
        self.assertTrue(len(props) > 0)

    def test_source_get_full_information_youtube(self):
        url = "https://www.youtube.com/watch?v=12312312"

        SourceDataController.objects.all().delete()

        props = SourceDataController.get_full_information({"url": url})

        self.assertTrue(props != None)
        self.assertTrue(len(props) > 0)
