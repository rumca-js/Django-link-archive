from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .utilities import WebPageDisabled
from ..pluginentries.entrypreviewcontroller import EntryPreviewController

from ..pluginentries.entryyoutubeplugin import EntryYouTubePlugin
from ..pluginentries.entryodyseeplugin import EntryOdyseePlugin
from ..pluginentries.entrygenericplugin import EntryGenericPlugin

from ..controllers import (
    LinkDataController,
)


class EntryUrlInterfaceTest(WebPageDisabled, TestCase):
    def setUp(self):
        self.disable_web_pages()

        ob = LinkDataController.objects.create(
            source="https://www.youtube.com",
            link="https://www.youtube.com/watch?v=123223",
            title="The second link",
            bookmarked=False,
            language="en",
        )
        # ob.date_published = days_before
        ob.save()

        ob = LinkDataController.objects.create(
            source="https://odysee.com",
            link="https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1",
            title="The second link",
            bookmarked=False,
            language="en",
        )

        ob = LinkDataController.objects.create(
            source="https://odysee.com",
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

        h = EntryPreviewController.get(entry)
        self.assertTrue(type(h) is EntryYouTubePlugin)

    def test_video_odysee_handler(self):
        entries = LinkDataController.objects.filter(
            link="https://odysee.com/@samtime:1/apple-reacts-to-leaked-windows-12:1"
        )
        entry = entries[0]

        h = EntryPreviewController.get(entry)
        self.assertTrue(type(h) is EntryOdyseePlugin)
