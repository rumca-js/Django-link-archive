from datetime import timedelta

import django.utils
from django.utils import timezone
from django.urls import reverse

from ..models import KeyWords
from ..configuration import Configuration
from .fakeinternet import FakeInternetTestCase


class KeyWordsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        c = Configuration.get_object().config_entry
        c.auto_store_keyword_info = True
        c.save()

        KeyWords.objects.all().delete()

    def is_key(self, keys, key):
        for inner in keys:
            if key == inner.keyword:
                return True

        return False

    def test_keywords_add_text(self):
        KeyWords.add_text(
            "Moment Russell Brand jokes about 'begging for threesomes' and having an 'orgy' with audience members in unearthed clip from his sold-out 'Shame' tour in 2006",
            "en",
        )

        keys = KeyWords.objects.all()

        for key in keys:
            print("Keyword: {}".format(key.keyword))

        self.assertTrue(keys.count() > 0)
        self.assertTrue(self.is_key(keys, "russell"))
        self.assertTrue(self.is_key(keys, "brand"))
        self.assertTrue(self.is_key(keys, "orgy"))
        self.assertTrue(self.is_key(keys, "audience"))
        self.assertTrue(self.is_key(keys, "members"))
        self.assertTrue(self.is_key(keys, "tour"))

    def test_keywords_add_link_data_ok(self):
        link_data = {
            "link": "http://youtube.com?v=whatever",
            "title": "nouns are good",
            "language": "en",
            "description": "description",
            "date_published": django.utils.timezone.now(),
        }

        KeyWords.add_link_data(link_data)

        keys = KeyWords.objects.all()

        for key in keys:
            print("Keyword: {}".format(key.keyword))

        self.assertTrue(keys.count() > 0)
        self.assertTrue(self.is_key(keys, "nouns"))

    def test_keywords_add_link_data_language_pl(self):
        link_data = {
            "link": "http://youtube.com?v=whatever",
            "title": "nouns are good",
            "language": "pl",
            "description": "description",
            "date_published": django.utils.timezone.now(),
        }

        KeyWords.add_link_data(link_data)

        keys = KeyWords.objects.all()
        self.assertEqual(keys.count(), 0)

    def test_keywords_add_link_data_language_none(self):
        link_data = {
            "link": "http://youtube.com?v=whatever",
            "title": "nouns are good",
            "description": "description",
            "date_published": django.utils.timezone.now(),
        }

        KeyWords.add_link_data(link_data)

        keys = KeyWords.objects.all()
        self.assertEqual(keys.count(), 0)

    def test_keywords_add_link_data_date_old(self):
        datetime = KeyWords.get_keywords_date_limit() - timedelta(days=1)

        link_data = {
            "link": "http://youtube.com?v=whatever",
            "title": "nouns are good",
            "language": "en",
            "description": "description",
            "date_published": datetime,
        }

        KeyWords.add_link_data(link_data)

        keys = KeyWords.objects.all()
        self.assertEqual(keys.count(), 0)

    def test_clear_old(self):
        datetime = KeyWords.get_keywords_date_limit() - timedelta(days=1)

        item = KeyWords.objects.create(keyword="test")
        item.date_published = datetime
        item.save()

        keys = KeyWords.objects.all()
        self.assertEqual(keys.count(), 1)

        KeyWords.cleanup()

        keys = KeyWords.objects.all()
        self.assertEqual(keys.count(), 0)
