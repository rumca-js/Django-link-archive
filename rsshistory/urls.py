
from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth
from django.views.generic import RedirectView
from . import views
from .viewspkg import viewentries, viewsources, viewcustom, viewtags, viewcomments

app_name = str(views.app_name)

urlpatterns = [
   path('', views.index, name='index'),

   # sources
   path('sources/', viewsources.RssSourceListView.as_view(), name='sources'),
   path('source/<int:pk>/', viewsources.RssSourceDetailView.as_view(), name='source-detail'),
   path('source-add', viewsources.add_source, name='source-add'),
   path('source-remove/<int:pk>/', viewsources.remove_source, name='source-remove'),
   path('source-edit/<int:pk>/', viewsources.edit_source, name='source-edit'),
   path('source-refresh/<int:pk>/', viewsources.refresh_source, name='source-refresh'),
   path('sources-remove-all/', viewsources.remove_all_sources, name='sources-remove-all'),
   path('sources-import', viewsources.import_sources, name='sources-import'),
   path('source-archive/<int:pk>/', viewsources.wayback_save, name='source-archive'),
   path('source-import-yt-links/<int:pk>/', viewsources.import_youtube_links_for_source, name='source-import-yt-links'),

   # entries
   path('entries/', viewentries.RssEntriesListView.as_view(), name='entries'),
   path('entry/<int:pk>/', viewentries.RssEntryDetailView.as_view(), name='entry-detail'),
   path('entry-add', viewentries.add_entry, name='entry-add'),
   path('entry-edit/<int:pk>/', viewentries.edit_entry, name='entry-edit'),
   path('entry-remove/<int:pk>/', viewentries.remove_entry, name='entry-remove'),
   path('entry-hide/<int:pk>/', viewentries.hide_entry, name='entry-hide'),
   path('entry-star/<int:pk>/', viewentries.make_persistent_entry, name='entry-star'),
   path('entry-notstar/<int:pk>/', viewentries.make_not_persistent_entry, name='entry-notstar'),
   path('entries-import', viewentries.import_entries, name='entries-import'),
   path('entries-untagged/', viewentries.NotBookmarkedView.as_view(), name='entries-untagged'),
   path('searchinitview', viewentries.search_init_view, name='searchinitview'),
   path('entry-download-music/<int:pk>/', viewcustom.download_music, name='entry-download-music'),
   path('entry-download-video/<int:pk>/', viewcustom.download_video, name='entry-download-video'),
   path('entry-download/<int:pk>/', viewentries.download_entry, name='entry-download'),
   path('entry-archive/<int:pk>/', viewentries.wayback_save, name='entry-archive'),

   # tags
   path('entry-tag/<int:pk>/', viewtags.tag_entry, name='entry-tag'),
   path('tag-remove/<int:pk>/', viewtags.tag_remove, name='tag-remove'),
   path('tags-entry-remove/<int:entrypk>/', viewtags.tags_entry_remove, name='tags-entry-remove'),
   path('tags-entry-show/<int:entrypk>/', viewtags.tags_entry_show, name='tags-entry-show'),
   path('tag-rename', viewtags.tag_rename, name='tag-rename'),
   path('show-tags', viewtags.show_tags, name='show-tags'),

   # comment
   path('entry-comment-add/<int:link_id>', viewcomments.entry_add_comment, name='entry-comment-add'),
   path('entry-comment-edit/<int:pk>/', viewcomments.entry_comment_edit, name='entry-comment-edit'),
   path('entry-comment-remove/<int:pk>/', viewcomments.entry_comment_remove, name='entry-comment-remove'),

   # custom views
   path('admin-page/', viewcustom.admin_page, name='admin-page'),
   path('user-config', viewcustom.user_config, name='user-config'),
   path('configuration/', viewcustom.configuration_page, name='configuration'),
   path('system-status/', viewcustom.system_status, name='system-status'),
   path('start-background-threads/', viewcustom.start_threads, name='start-background-threads'),
   path('backgroundjobs/', viewcustom.BackgroundJobsView.as_view(), name='backgroundjobs'),
   path('write-bookmarks', viewcustom.write_bookmarks, name='write-bookmarks'),
   path('write-daily-data-form', viewcustom.write_daily_data_form, name='write-daily-data-form'),
   path('write-tag-form', viewcustom.write_tag_form, name='write-tag-form'),
   path('import-reading-list', viewcustom.import_reading_list_view, name='import-reading-list'),
   path('import-source-ia/<int:pk>/', viewcustom.import_source_from_ia, name='import-source-ia'),
   path('truncate-errors', viewcustom.truncate_errors, name='truncate-errors'),
   path('data-errors', viewcustom.data_errors_page, name='data-errors'),
   path('entry-fix-youtube-details/<int:pk>/', viewcustom.fix_reset_youtube_link_details_page, name='entry-fix-youtube-details'),
   path('fix-entry-tags/<int:entrypk>/', viewcustom.fix_entry_tags, name='fix-entry-tags'),
   path('fix-source-entries-lan/<int:pk>/', viewcustom.fix_source_entries_language, name='fix-source-entries-lan'),
   path('show-yt-props', viewcustom.show_youtube_link_props, name='show-youtube-link-props'),
   path('test-page', viewcustom.test_page, name='test-page'),
   path('fix-bookmarked-yt', viewcustom.fix_bookmarked_yt, name='fix-bookmarked-yt'),
   path('clear-yt-cache', viewcustom.clear_youtube_cache, name='clear-yt-cache'),

   # login
   path('accounts/', include('django.contrib.auth.urls')),
   path('rsshistory/accounts/logout/', RedirectView.as_view(url='rsshistory/')),
   path('accounts/logout/', RedirectView.as_view(url='rsshistory/')),
]
