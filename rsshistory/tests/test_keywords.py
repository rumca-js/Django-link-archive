from pathlib import Path
from datetime import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..models import KeyWords


class KeyWordsTest(TestCase):

    def test_keywords_add_text(self):
        KeyWords.add_text("Moment Russell Brand jokes about 'begging for threesomes' and having an 'orgy' with audience members in unearthed clip from his sold-out 'Shame' tour in 2006", "en")

        keys = KeyWords.objects.all()

        for key in keys:
            print("Keyword: {}".format(key.keyword))

        self.assertTrue(keys.count() > 0)
