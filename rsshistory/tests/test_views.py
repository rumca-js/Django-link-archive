from django.urls import reverse

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport

from .fakeinternet import FakeInternetTestCase


class ViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_index(self):
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

    def test_source_save(self):
        url = reverse("{}:source-save".format(LinkDatabase.name), args=[0])
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

    def test_sources_refresh_all(self):
        url = reverse("{}:sources-manual-refresh".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    """
    Entries
    """

    def test_entries(self):
        url = reverse("{}:entries".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_recent(self):
        url = reverse("{}:entries-recent".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_untagged(self):
        url = reverse("{}:entries-untagged".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_bookmarked(self):
        url = reverse("{}:entries-bookmarked".format(LinkDatabase.name))
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

    def test_entry_add_simple(self):
        url = reverse("{}:entry-add-simple".format(LinkDatabase.name))
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

    def test_entry_dead(self):
        url = reverse("{}:entry-dead".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_not_dead(self):
        url = reverse("{}:entry-not-dead".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_bookmark(self):
        url = reverse("{}:entry-bookmark".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_nobookmark(self):
        url = reverse("{}:entry-notbookmark".format(LinkDatabase.name), args=[0])
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

    def test_entry_save(self):
        url = reverse("{}:entry-save".format(LinkDatabase.name), args=[0])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_untagged(self):
        url = reverse("{}:entries-untagged".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_search_init(self):
        url = reverse("{}:entries-search-init".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_bookmarked_init(self):
        url = reverse("{}:entries-bookmarked-init".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_recent_init(self):
        url = reverse("{}:entries-recent-init".format(LinkDatabase.name))
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
    System views
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

    def test_about(self):
        url = reverse("{}:about".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_reset_config(self):
        url = reverse("{}:reset-config".format(LinkDatabase.name))
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

    """
    Other views
    """

    def test_show_page_props(self):
        url = reverse("{}:page-show-props".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_show_page_props_html(self):
        url = (
            reverse("{}:page-show-props".format(LinkDatabase.name))
            + "?page=https://www.linkedin.com"
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_show_youtube_link_props(self):
        url = (
            reverse("{}:page-show-props".format(LinkDatabase.name))
            + "?page=https://www.youtube.com/watch?v=SwlIAjcYypA"
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_show_rss_link_props(self):
        url = (
            reverse("{}:page-show-props".format(LinkDatabase.name))
            + "?page=https://www.youtube.com/feeds/samtime.rss"
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_page_scanner(self):
        url = reverse("{}:page-scan".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_page_scanner_input(self):
        url = reverse("{}:page-scan-input".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_page_scanner_input_html(self):
        url = (
            reverse("{}:page-scan-input".format(LinkDatabase.name))
            + "?link=https://www.linkedin.com"
        )
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

    def test_check_move_archive(self):
        url = reverse("{}:check-move-archive".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_push_daily_data_form(self):
        url = reverse("{}:push-daily-data-form".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_domains(self):
        url = reverse("{}:domains".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    # Note: do not test import, as it starts importing
    #
    # def test_import_reading_list(self):
    #    url = reverse("{}:import-reading-list".format(LinkDatabase.name))
    #    resp = self.client.get(url)
    #
    #    self.assertEqual(resp.status_code, 200)


class EnhancedViewTest(ViewsTest):
    def setUp(self):
        self.disable_web_pages()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )

        domain = DomainsController.objects.create(
            domain="https://youtube.com",
        )
        domain.date_created = DateUtils.from_string(
            "2023-03-03;16:34", "%Y-%m-%d;%H:%M"
        )
        domain.save()

        keyword = KeyWords.objects.create(keyword="test")

        self.export_daily = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.export_year = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.export_notime = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

    def test_entry(self):
        url = reverse(
            "{}:entry-detail".format(LinkDatabase.name),
            args=[LinkDataController.objects.all()[0].id],
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_source(self):
        url = reverse(
            "{}:source-detail".format(LinkDatabase.name),
            args=[SourceDataController.objects.all()[0].id],
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_source_json(self):
        sources = SourceDataController.objects.filter(url__icontains="https://youtube")

        url = reverse("{}:source-json".format(LinkDatabase.name), args=[sources[0].id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_sources_json(self):
        sources = SourceDataController.objects.filter(url__icontains="https://youtube")

        url = reverse("{}:sources-json".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entry_json(self):
        entries = LinkDataController.objects.filter(link__icontains="https://youtube")

        url = reverse("{}:entry-json".format(LinkDatabase.name), args=[entries[0].id])
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

    def test_entries_json(self):
        entries = LinkDataController.objects.filter(link__icontains="https://youtube")

        url = reverse("{}:entries-json".format(LinkDatabase.name))
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
