from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..apps import LinkDatabase


class ViewsTest(TestCase):
    def test_index(self):
        #    w = self.create_whatever()
        url = reverse("{}:index".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    """
    Sources
    """

    def test_sources(self):
        url = reverse("{}:sources".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source(self):
        url = reverse("{}:source-detail".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)

    def test_source_add(self):
        url = reverse("{}:source-add".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source_remove(self):
        url = reverse("{}:source-remove".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source_edit(self):
        url = reverse("{}:source-edit".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source_refresh(self):
        url = reverse("{}:source-refresh".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source_archive(self):
        url = reverse("{}:source-archive".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source_import_yt_links(self):
        url = reverse("{}:source-import-yt-links".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source_process_text(self):
        url = reverse("{}:source-process-text".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_source_remove_all(self):
        url = reverse("{}:sources-remove-all".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    """
    Entries
    """

    def test_entries(self):
        url = reverse("{}:entries".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry(self):
        url = reverse("{}:entry-detail".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)

    def test_entry_add(self):
        url = reverse("{}:entry-add".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_edit(self):
        url = reverse("{}:entry-edit".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_remove(self):
        url = reverse("{}:entry-remove".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_hide(self):
        url = reverse("{}:entry-hide".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_star(self):
        url = reverse("{}:entry-star".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_nostar(self):
        url = reverse("{}:entry-nostar".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_nostar(self):
        url = reverse("{}:entry-notstar".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_download_music(self):
        url = reverse("{}:entry-download-music".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_download_video(self):
        url = reverse("{}:entry-download-video".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_download(self):
        url = reverse("{}:entry-download".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_archive(self):
        url = reverse("{}:entry-archive".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_untagged(self):
        url = reverse("{}:entries-untagged".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_search(self):
        url = reverse("{}:searchinitview".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    """
    Tags
    """

    def test_tag_entry(self):
        url = reverse("{}:entry-tag".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tag_remove(self):
        url = reverse("{}:tag-remove".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tag_entry_remove(self):
        url = reverse("{}:tags-entry-remove".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tag_entry_show(self):
        url = reverse("{}:tags-entry-show".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tag_rename(self):
        url = reverse("{}:tag-rename".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tag_show_all(self):
        url = reverse("{}:tags-show-all".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_tag_show_recent(self):
        url = reverse("{}:tags-show-recent".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    """
    Comments
    """

    def test_comment_add(self):
        url = reverse("{}:entry-comment-add".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_comment_edit(self):
        url = reverse("{}:entry-comment-edit".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_comment_remove(self):
        url = reverse("{}:entry-comment-remove".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    """
    Other views
    """

    def test_admin(self):
        url = reverse("{}:admin-page".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_user_config(self):
        url = reverse("{}:user-config".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_configuration(self):
        url = reverse("{}:configuration".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_system_status(self):
        url = reverse("{}:system-status".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_system_status(self):
        url = reverse("{}:system-status".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_backgroundjobs(self):
        url = reverse("{}:backgroundjobs".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_backgroundjob_remove(self):
        url = reverse("{}:backgroundjob-remove".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_backgroundjobs_remove(self):
        url = reverse("{}:backgroundjobs-remove".format(LinkDatabase.name), args=["0"])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_shot_yt_props(self):
        url = reverse("{}:show-youtube-link-props".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_import_bookmarks(self):
        url = reverse("{}:import-bookmarks".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_import_daily_data(self):
        url = reverse("{}:import-daily-data".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_import_sources(self):
        url = reverse("{}:import-sources".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    # def test_import_reading_list(self):
    #    url = reverse("{}:import-reading-list".format(LinkDatabase.name))
    #    resp = self.client.get(url)

    #    self.assertEqual(resp.status_code, 200)
