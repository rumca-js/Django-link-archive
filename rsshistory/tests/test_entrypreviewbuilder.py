from ..viewspkg.plugins import EntryPreviewBuilder
from ..viewspkg.plugins import EntryYouTubePlugin
from ..viewspkg.plugins import EntryOdyseePlugin
from ..viewspkg.plugins import EntryGenericPlugin

from ..controllers import (
    LinkDataController,
)

from .fakeinternet import FakeInternetTestCase


class EntryUrlInterfaceTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        ob = LinkDataController.objects.create(
            source_url="https://www.youtube.com",
            link="https://www.youtube.com/watch?v=123223",
            title="The second link",
            bookmarked=False,
            language="en",
        )

        ob = LinkDataController.objects.create(
            source_url="https://odysee.com",
            link="https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1",
            title="The second link",
            bookmarked=False,
            language="en",
        )

        ob = LinkDataController.objects.create(
            source_url="https://odysee.com",
            link="https://odysee.com/@samtime:1",
            title="The second link",
            bookmarked=False,
            language="en",
        )

    def test_video_youtube_handler(self):
        entries = LinkDataController.objects.filter(
            link__icontains="https://www.youtube.com/watch?"
        )
        entry = entries[0]

        h = EntryPreviewBuilder.get(entry)
        self.assertTrue(type(h) is EntryYouTubePlugin)

    def test_video_odysee_handler(self):
        entries = LinkDataController.objects.filter(
            link="https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1"
        )
        entry = entries[0]

        h = EntryPreviewBuilder.get(entry)
        self.assertTrue(type(h) is EntryOdyseePlugin)
