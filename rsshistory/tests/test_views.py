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

    def test_admin(self):
        url = reverse("rsshistory:admin-page")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_user_config(self):
        url = reverse("rsshistory:user-config")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_system_status(self):
        url = reverse("rsshistory:system-status")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_backgroundjobs(self):
        url = reverse("rsshistory:backgroundjobs")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_configuration(self):
        url = reverse("rsshistory:configuration")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tags_show_all(self):
        url = reverse("rsshistory:tags-show-all")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tags_show_recent(self):
        url = reverse("rsshistory:tags-show-recent")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tag_rename(self):
        url = reverse("rsshistory:tag-rename")
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
