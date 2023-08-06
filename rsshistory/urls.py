from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

from . import views
from .apps import LinkDatabase
from .viewspkg import viewentries, viewsources, viewcustom, viewtags, viewcomments

# register app namespace
# TODO https://stackoverflow.com/questions/30494000/django-url-namespaces-the-template-has-to-know-its-namespace
app_name = str(LinkDatabase.name)

# fmt: off
urlpatterns = [
    path("", views.index, name="index"),
    # sources
    path("sources/", viewsources.RssSourceListView.as_view(), name="sources"),
    path("source/<int:pk>/", viewsources.RssSourceDetailView.as_view(), name="source-detail"),
    path("sources-json/", viewsources.sources_json, name="sources-json"),
    path("source-add", viewsources.add_source, name="source-add"),
    path("source-add-simple", viewsources.add_source_simple, name="source-add-simple"),
    path("source-remove/<int:pk>/", viewsources.remove_source, name="source-remove"),
    path("source-remove-entries/<int:pk>/", viewsources.source_remove_entries, name="source-remove-entries"),
    path("source-edit/<int:pk>/", viewsources.edit_source, name="source-edit"),
    path("source-refresh/<int:pk>/", viewsources.refresh_source, name="source-refresh"),
    path("source-archive/<int:pk>/", viewsources.wayback_save, name="source-archive"),
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
    path("entry/<int:pk>/", viewentries.EntryDetailView.as_view(), name="entry-detail"),
    path("entry-archived/<int:pk>/", viewentries.EntryArchivedDetailView.as_view(), name="entry-archived"),
    path("entry-add", viewentries.add_entry, name="entry-add"),
    path("entry-add-simple", viewentries.add_simple_entry, name="entry-add-simple"),
    path("entry-edit/<int:pk>/", viewentries.edit_entry, name="entry-edit"),
    path("entry-remove/<int:pk>/", viewentries.remove_entry, name="entry-remove"),
    path("entry-hide/<int:pk>/", viewentries.hide_entry, name="entry-hide"),
    path("entry-star/<int:pk>/", viewentries.make_persistent_entry, name="entry-star"),
    path("entry-notstar/<int:pk>/", viewentries.make_not_persistent_entry, name="entry-notstar"),
    path("entry-download-music/<int:pk>/", viewcustom.download_music, name="entry-download-music",),
    path("entry-download-video/<int:pk>/", viewcustom.download_video, name="entry-download-video",),
    path("entry-download/<int:pk>/", viewentries.download_entry, name="entry-download"),
    path("entry-archive/<int:pk>/", viewentries.wayback_save, name="entry-archive"),
    # tags
    path("entry-tag/<int:pk>/", viewtags.tag_entry, name="entry-tag"),
    path("tag-remove/<int:pk>/", viewtags.tag_remove, name="tag-remove"),
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
    path("admin-page/", viewcustom.admin_page, name="admin-page"),
    path("user-config", viewcustom.user_config, name="user-config"),
    path("configuration/", viewcustom.configuration_page, name="configuration"),
    path("system-status/", viewcustom.system_status, name="system-status"),
    path("about/", viewcustom.about, name="about"),
    # background jobs
    path("backgroundjobs/", viewcustom.BackgroundJobsView.as_view(), name="backgroundjobs",),
    path("backgroundjobs-perform-all/", viewcustom.backgroundjobs_perform_all, name="backgroundjobs-perform-all",),
    path("backgroundjob-remove/<int:pk>/", viewcustom.backgroundjob_remove, name="backgroundjob-remove",),
    path("backgroundjobs-remove/<str:job_type>/", viewcustom.backgroundjobs_remove, name="backgroundjobs-remove",),
    path("write-bookmarks", viewcustom.write_bookmarks, name="write-bookmarks"),
    path("write-daily-data-form", viewcustom.write_daily_data_form, name="write-daily-data-form",),
    path("write-tag-form", viewcustom.write_tag_form, name="write-tag-form"),
    path("push-daily-data-form", viewcustom.push_daily_data_form, name="push-daily-data-form"),
    path("import-bookmarks", viewcustom.import_bookmarks, name="import-bookmarks"),
    path("import-daily-data", viewcustom.import_daily_data, name="import-daily-data"),
    path("import-sources", viewcustom.import_sources, name="import-sources"),
    path("import-reading-list", viewcustom.import_reading_list_view, name="import-reading-list",),
    path("check-move-archive", viewcustom.check_if_move_to_archive, name="check-move-archive",),
    # persistant infos
    path("persistentinfos/", viewcustom.PersistentInfoView.as_view(), name="persistentinfos",),
    # domains
    path("domains/", viewcustom.DomainsListView.as_view(), name="domains",),
    path("domain-remove/<int:pk>/", viewcustom.domain_remove, name="domain-remove",),
    path("domains-fix/", viewcustom.domains_fix, name="domain-fix",),
    # debug forms
    path("import-source-ia/<int:pk>/", viewcustom.import_source_from_ia, name="import-source-ia",),
    path("truncate-errors", viewcustom.truncate_errors, name="truncate-errors"),
    path("data-errors", viewcustom.data_errors_page, name="data-errors"),
    path("entry-fix-youtube-details/<int:pk>/", viewcustom.fix_reset_youtube_link_details_page, name="entry-fix-youtube-details",),
    path("fix-entry-tags/<int:entrypk>/", viewcustom.fix_entry_tags, name="fix-entry-tags",),
    path("show-yt-props", viewcustom.show_youtube_link_props, name="show-youtube-link-props",),
    path("test-page", viewcustom.test_page, name="test-page"),
    path("test-form-page", viewcustom.test_form_page, name="test-form-page"),
    path("fix-bookmarked-yt", viewcustom.fix_bookmarked_yt, name="fix-bookmarked-yt"),
    path("clear-yt-cache", viewcustom.clear_youtube_cache, name="clear-yt-cache"),
    # login
    path("accounts/", include("django.contrib.auth.urls")),
    path("rsshistory/accounts/logout/", RedirectView.as_view(url="rsshistory/")),
    path("accounts/logout/", RedirectView.as_view(url="rsshistory/")),
]
# fmt: on
