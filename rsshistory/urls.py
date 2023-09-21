from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

from . import views
from .apps import LinkDatabase
from .viewspkg import (
    viewentries,
    viewsources,
    viewcustom,
    viewtags,
    viewcomments,
    viewadmin,
    viewexport,
    viewdomains,
)

# register app namespace
# TODO https://stackoverflow.com/questions/30494000/django-url-namespaces-the-template-has-to-know-its-namespace
app_name = str(LinkDatabase.name)

# fmt: off
urlpatterns = [
    path("", views.index, name="index"),
    # sources
    path("sources/", viewsources.RssSourceListView.as_view(), name="sources"),
    path("source/<int:pk>/", viewsources.RssSourceDetailView.as_view(), name="source-detail"),
    path("source-json/<int:pk>", viewsources.source_json, name="source-json"),
    path("sources-json/", viewsources.sources_json, name="sources-json"),
    path("source-add", viewsources.add_source, name="source-add"),
    path("source-add-simple", viewsources.add_source_simple, name="source-add-simple"),
    path("source-remove/<int:pk>/", viewsources.remove_source, name="source-remove"),
    path("source-remove-entries/<int:pk>/", viewsources.source_remove_entries, name="source-remove-entries"),
    path("source-edit/<int:pk>/", viewsources.edit_source, name="source-edit"),
    path("source-refresh/<int:pk>/", viewsources.refresh_source, name="source-refresh"),
    path("source-save/<int:pk>/", viewsources.wayback_save, name="source-save"),
    path("source-import-yt-links/<int:pk>/", viewsources.import_youtube_links_for_source, name="source-import-yt-links"),
    path("source-process-text/<int:pk>/", viewsources.process_source_text, name="source-process-text"),
    path("source-fix-entries/<int:source_pk>/", viewsources.source_fix_entries, name="source-fix-entries",),
    path("sources-remove-all/", viewsources.remove_all_sources, name="sources-remove-all"),
    path("sources-manual-refresh/", viewsources.sources_manual_refresh, name="sources-manual-refresh"),
    # entries
    path("entries/", viewentries.EntriesSearchListView.as_view(), name="entries"),
    path("entries-recent/", viewentries.EntriesRecentListView.as_view(), name="entries-recent"),
    path("entries-archived/", viewentries.EntriesArchiveListView.as_view(), name="entries-archived"),
    path("entries-untagged/", viewentries.EntriesNotTaggedView.as_view(), name="entries-untagged"),
    path("entries-bookmarked/", viewentries.EntriesBookmarkedListView.as_view(), name="entries-bookmarked"),
    path("entries-json/", viewentries.entries_json, name="entries-json"),
    path("entries-omni-search-init", viewentries.entries_omni_search_init, name="entries-omni-search-init"),
    path("entries-search-init", viewentries.entries_search_init, name="entries-search-init"),
    path("entries-archived-init", viewentries.entries_archived_init, name="entries-archived-init"),
    path("entries-bookmarked-init", viewentries.entries_bookmarked_init, name="entries-bookmarked-init"),
    path("entries-recent-init", viewentries.entries_recent_init, name="entries-recent-init"),
    path("entries-omni-search", viewentries.EntriesOmniListView.as_view(), name="entries-omni-search"),
    path("entries-remove-all", viewentries.entries_remove_all, name="entries-remove-all"),
    path("entries-remove-nonbookmarked", viewentries.entries_remove_nonbookmarked, name="entries-remove-nonbookmarked"),
    path("entry/<int:pk>/", viewentries.EntryDetailView.as_view(), name="entry-detail"),
    path("entry-json/<int:pk>/", viewentries.entry_json, name="entry-json"),
    path("entry-archived/<int:pk>/", viewentries.EntryArchivedDetailView.as_view(), name="entry-archived"),
    path("entry-add", viewentries.add_entry, name="entry-add"),
    path("entry-add-simple", viewentries.add_simple_entry, name="entry-add-simple"),
    path("entry-edit/<int:pk>/", viewentries.edit_entry, name="entry-edit"),
    path("entry-remove/<int:pk>/", viewentries.remove_entry, name="entry-remove"),
    path("entry-hide/<int:pk>/", viewentries.hide_entry, name="entry-hide"),
    path("entry-bookmark/<int:pk>/", viewentries.make_bookmarked_entry, name="entry-bookmark"),
    path("entry-notbookmark/<int:pk>/", viewentries.make_not_bookmarked_entry, name="entry-notbookmark"),
    path("entry-download-music/<int:pk>/", viewcustom.download_music, name="entry-download-music",),
    path("entry-download-video/<int:pk>/", viewcustom.download_video, name="entry-download-video",),
    path("entry-download/<int:pk>/", viewentries.download_entry, name="entry-download"),
    path("entry-archive-edit/<int:pk>/", viewentries.archive_edit_entry, name="entry-archive-edit"),
    path("entry-archive-bookmark/<int:pk>/", viewentries.archive_make_bookmarked_entry, name="entry-archive-bookmark"),
    path("entry-archive-notbookmark/<int:pk>/", viewentries.archive_make_not_bookmarked_entry, name="entry-archive-notbookmark"),
    path("entry-archive-hide/<int:pk>/", viewentries.archive_hide_entry, name="entry-archive-hide"),
    path("entry-archive-remove/<int:pk>/", viewentries.archive_remove_entry, name="entry-archive-remove"),
    path("entry-save/<int:pk>/", viewentries.wayback_save, name="entry-save"),
    # tags
    path("entry-tag/<int:pk>/", viewtags.tag_entry, name="entry-tag"),
    path("tag-remove/<int:pk>/", viewtags.tag_remove, name="tag-remove"),
    path("tag-remove-str/<str:tag>/", viewtags.tag_remove_str, name="tag-remove-str"),
    path("tag-remove-form/", viewtags.tag_remove_form, name="tag-remove-form"),
    path("tags-entry-remove/<int:entrypk>/", viewtags.tags_entry_remove, name="tags-entry-remove",),
    path("tags-entry-show/<int:entrypk>/", viewtags.tags_entry_show, name="tags-entry-show",),
    path("tag-rename", viewtags.tag_rename, name="tag-rename"),
    path("tags-show-all", viewtags.AllTags.as_view(), name="tags-show-all"),
    path("tags-show-recent", viewtags.RecentTags.as_view(), name="tags-show-recent"),
    # comment
    path("entry-comment-add/<int:link_id>", viewcomments.entry_add_comment, name="entry-comment-add",),
    path("entry-comment-edit/<int:pk>/", viewcomments.entry_comment_edit, name="entry-comment-edit",),
    path("entry-comment-remove/<int:pk>/", viewcomments.entry_comment_remove, name="entry-comment-remove",),
    # vote
    path("entry-vote/<int:pk>/", viewtags.entry_vote, name="entry-vote"),
    # admin views
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("admin-page/", viewadmin.admin_page, name="admin-page"),
    path("user-config", viewadmin.user_config, name="user-config"),
    path("configuration/", viewadmin.configuration_page, name="configuration"),
    path("system-status/", viewadmin.system_status, name="system-status"),
    path("about/", viewadmin.about, name="about"),
    path("missing-rights/", viewadmin.missing_rights, name="missing-rights"),
    path("show-info/", viewcustom.show_info, name="show-info"),
    # background jobs
    path("backgroundjobs/", viewadmin.BackgroundJobsView.as_view(), name="backgroundjobs",),
    path("backgroundjob-add", viewadmin.backgroundjob_add, name="backgroundjob-add",),
    path("backgroundjobs-check-new/", viewadmin.backgroundjobs_check_new, name="backgroundjobs-check-new",),
    path("backgroundjobs-perform-all/", viewadmin.backgroundjobs_perform_all, name="backgroundjobs-perform-all",),
    path("backgroundjob-remove/<int:pk>/", viewadmin.backgroundjob_remove, name="backgroundjob-remove",),
    path("backgroundjobs-remove/<str:job_type>/", viewadmin.backgroundjobs_remove, name="backgroundjobs-remove",),
    path("backgroundjobs-remove-all/", viewadmin.backgroundjobs_remove_all, name="backgroundjobs-remove-all",),
    # persistant infos
    path("logs/", viewadmin.PersistentInfoView.as_view(), name="logs",),
    path("truncate-log", viewadmin.truncate_log, name="truncate-log"),
    path("truncate-log-errors", viewadmin.truncate_log_errors, name="truncate-log-errors"),
    path("truncate-log-all", viewadmin.truncate_log_all, name="truncate-log-all"),
    # import / export
    path("data-export-add", viewexport.data_export_add, name="data-export-add"),
    path("data-export-edit/<int:pk>/", viewexport.data_export_edit, name="data-export-edit"),
    path("data-export-remove/<int:pk>/", viewexport.data_export_remove, name="data-export-remove"),
    path("data-exports/", viewexport.DataExportListView.as_view(), name="data-exports",),
    path("data-export/<int:pk>/", viewexport.DataExportDetailsView.as_view(), name="data-export",),
    path("write-bookmarks", viewexport.write_bookmarks, name="write-bookmarks"),
    path("write-daily-data-form", viewexport.write_daily_data_form, name="write-daily-data-form",),
    path("write-tag-form", viewexport.write_tag_form, name="write-tag-form"),
    path("push-daily-data-form", viewexport.push_daily_data_form, name="push-daily-data-form"),
    path("import-bookmarks", viewexport.import_bookmarks, name="import-bookmarks"),
    path("import-daily-data", viewexport.import_daily_data, name="import-daily-data"),
    path("import-sources", viewexport.import_sources, name="import-sources"),
    path("import-reading-list", viewexport.import_reading_list_view, name="import-reading-list",),
    path("import-from-instance", viewexport.import_from_instance, name="import-from-instance",),
    path("import-source-ia/<int:pk>/", viewexport.import_source_from_ia, name="import-source-ia",),
    # domains
    path("domains/", viewdomains.DomainsListView.as_view(), name="domains",),
    path("domain/<int:pk>/", viewdomains.DomainsDetailView.as_view(), name="domain-detail",),
    path("domain-by-name/", viewdomains.DomainsByNameDetailView.as_view(), name="domain-by-name",),
    path("domain-add/", viewdomains.domain_add, name="domain-add",),
    path("domain-edit/<int:pk>/", viewdomains.domain_edit, name="domain-edit",),
    path("domain-remove/<int:pk>/", viewdomains.domain_remove, name="domain-remove",),
    path("domains-remove-all/", viewdomains.domains_remove_all, name="domains-remove-all",),
    path("domains-fix/", viewdomains.domains_fix, name="domains-fix",),
    path("domain-update-data/<int:pk>/", viewdomains.domain_update_data, name="domain-update-data",),
    path("domains-read-bookmarks/", viewdomains.domains_read_bookmarks, name="domains-read-bookmarks",),
    path("domain-json/<int:pk>/", viewdomains.domain_json, name="domain-json",),
    path("domains-json/", viewdomains.domains_json, name="domains-json"),
    path("domain-category-list/", viewdomains.domain_category_list, name="domain-category-list"),
    # keywords
    path("keywords/", viewentries.keywords, name="keywords",),
    path("keywords-remove-all/", viewentries.keywords_remove_all, name="keywords-remove-all",),
    # other, debug forms
    path("check-move-archive", viewcustom.check_if_move_to_archive, name="check-move-archive",),
    path("data-errors", viewcustom.data_errors_page, name="data-errors"),
    path("entry-fix-youtube-details/<int:pk>/", viewcustom.fix_reset_youtube_link_details_page, name="entry-fix-youtube-details",),
    path("fix-entry-tags/<int:entrypk>/", viewcustom.fix_entry_tags, name="fix-entry-tags",),
    path("show-yt-props", viewcustom.show_youtube_link_props, name="show-youtube-link-props",),
    path("show-page-props", viewcustom.show_page_props, name="show-page-props",),
    path("test-page", viewcustom.test_page, name="test-page"),
    path("test-form-page", viewcustom.test_form_page, name="test-form-page"),
    path("fix-bookmarked-yt", viewcustom.fix_bookmarked_yt, name="fix-bookmarked-yt"),
    # login
    path("accounts/", include("django.contrib.auth.urls")),
    path("rsshistory/accounts/logout/", RedirectView.as_view(url="rsshistory/")),
    path("accounts/logout/", RedirectView.as_view(url="rsshistory/")),
]
# fmt: on
