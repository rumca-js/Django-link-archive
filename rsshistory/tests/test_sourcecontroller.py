from ..controllers import (
    SourceDataController,
    SourceDataBuilder,
    BackgroundJobController,
)

from .fakeinternet import FakeInternetTestCase


class SourceControllerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        SourceDataController.objects.all().delete()

    def test_new_source_automatic(self):
        # call tested function
        source = SourceDataBuilder(
            link_data={
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            },
            manual_entry = False,
        ).add_from_props()

        # automatic entry creates on_hold sources, that are not fetched
        sources = SourceDataController.objects.all()
        self.assertEqual(sources.count(), 1)
        self.assertEqual(sources[0].on_hold, True)

        self.assertEqual(BackgroundJobController.objects.all().count(), 0)

    def test_new_source_manual(self):
        # call tested function
        SourceDataBuilder(
            link_data={
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            },
            manual_entry = True,
        ).add_from_props()

        # manual entry adds a new active source, that is fetched
        sources = SourceDataController.objects.all()
        self.assertEqual(sources.count(), 1)
        self.assertEqual(sources[0].on_hold, False)

        self.assertEqual(BackgroundJobController.objects.all().count(), 1)

    def test_new_source_twice(self):
        # call tested function
        SourceDataBuilder(
            link_data={
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }
        )

        # call tested function
        b = SourceDataBuilder()

        b.link_data={
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
            }

        source = b.add_from_props()

        self.assertTrue(not source)
        self.assertEqual(SourceDataController.objects.all().count(), 1)

    def test_add_source_from_props_favicon(self):
        self.assertEqual(SourceDataController.objects.all().count(), 0)

        # call tested function
        b = SourceDataBuilder()
        b.link_data={
                "url": "https://linkedin.com",
                "title": "LinkedIn",
                "category": "No",
                "subcategory": "No",
                "export_to_cms": False,
                "favicon": "https://linkedin.com/images/favicon.ico",
            }
        source = b.add_from_props()

        self.print_errors()

        self.assertEqual(SourceDataController.objects.all().count(), 1)
        self.assertTrue(source)

        self.assertTrue(
            source.get_favicon() == "https://linkedin.com/images/favicon.ico"
        )

    def test_source_get_full_information_page(self):
        url = "https://linkedin.com"

        # call tested function
        props = SourceDataController.get_full_information({"url": url})

        self.assertTrue(props != None)
        self.assertTrue(len(props) > 0)

    def test_source_get_full_information_youtube(self):
        url = "https://www.youtube.com/watch?v=12312312"

        # call tested function
        props = SourceDataController.get_full_information({"url": url})

        self.assertTrue(props != None)
        self.assertTrue(len(props) > 0)
