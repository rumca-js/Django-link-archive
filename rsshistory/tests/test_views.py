from django.test import TestCase
from django.utils import timezone
from django.urls import reverse


class ViewsTest(TestCase):

    def test_index(self):
    #    w = self.create_whatever()
        url = reverse("rsshistory:index")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_sources(self):
        url = reverse("rsshistory:sources")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source(self):
        url = reverse("rsshistory:source-detail", args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)

    def test_source_add(self):
        url = reverse("rsshistory:source-add")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries(self):
        url = reverse("rsshistory:entries")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry(self):
        url = reverse("rsshistory:entry-detail", args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)

    def test_entry_add(self):
        url = reverse("rsshistory:entry-add")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_configuration(self):
        url = reverse("rsshistory:configuration")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_status(self):
        url = reverse("rsshistory:system-status")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_search_init_view(self):
        url = reverse("rsshistory:searchinitview")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_show_tags(self):
        url = reverse("rsshistory:show-tags")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)