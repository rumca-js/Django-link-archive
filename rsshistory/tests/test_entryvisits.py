
from ..models import EntryVisits
from ..controllers import LinkDataController, SourceDataController
from .fakeinternet import FakeInternetTestCase


class EntryVisitsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        ob = SourceDataController.objects.create(
            url="https://youtube.com", title="YouTube", category="No", subcategory="No"
        )

        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=12345",
            source_obj=ob,
        )

    def test_entry_visit(self):
        entries = LinkDataController.objects.filter(link="https://youtube.com?v=12345")

        EntryVisits.visited(entries[0], "test_username")

        visits = EntryVisits.objects.filter(entry="https://youtube.com?v=12345")
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 1)
        self.assertEqual(visits[0].user, "test_username")

        EntryVisits.visited(entries[0], "test_username")

        visits = EntryVisits.objects.filter(entry="https://youtube.com?v=12345")
        self.assertEqual(visits.count(), 1)
        self.assertEqual(visits[0].visits, 2)
        self.assertEqual(visits[0].user, "test_username")
