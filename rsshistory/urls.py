
from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth
from django.views.generic import RedirectView
from . import views
from .viewspkg import viewentries, viewsources, viewcustom

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
   path('sources-export/', viewsources.export_sources, name='sources-export'),
   path('source-wayback-save/<int:pk>/', viewsources.wayback_save, name='source-wayback-save'),

   # entries
   path('entries/', viewentries.RssEntriesListView.as_view(), name='entries'),
   path('entry/<int:pk>/', viewentries.RssEntryDetailView.as_view(), name='entry-detail'),
   path('entry-add', viewentries.add_entry, name='entry-add'),
   path('entry-edit/<int:pk>/', viewentries.edit_entry, name='entry-edit'),
   path('entry-remove/<int:pk>/', viewentries.remove_entry, name='entry-remove'),
   path('entry-hide/<int:pk>/', viewentries.hide_entry, name='entry-hide'),
   path('entry-star/<int:pk>/', viewentries.make_persistent_entry, name='entry-star'),
   path('entry-notstar/<int:pk>/', viewentries.make_not_persistent_entry, name='entry-notstar'),
   path('entry-tag/<int:pk>/', viewentries.tag_entry, name='entry-tag'),
   path('entries-import', viewentries.import_entries, name='entries-import'),
   path('entries-untagged/', viewentries.NotBookmarkedView.as_view(), name='entries-untagged'),
   path('searchinitview', viewentries.search_init_view, name='searchinitview'),

   # comment
   path('entry-comment-add/<int:link_id>', views.entry_add_comment, name='entry-comment-add'),
   path('entry-comment-edit/<int:pk>/', views.entry_comment_edit, name='entry-comment-edit'),
   path('entry-comment-remove/<int:pk>/', views.entry_comment_remove, name='entry-comment-remove'),

   # custom views
   path('configuration/', viewcustom.configuration, name='configuration'),
   path('system-status/', viewcustom.system_status, name='system-status'),
   path('start-background-threads/', viewcustom.start_threads, name='start-background-threads'),
   path('import-view', viewcustom.import_view, name='import-view'),
   path('import-source-ia/<int:pk>/', viewcustom.import_source_from_ia, name='import-source-ia'),
   path('truncate-errors', viewcustom.truncate_errors, name='truncate-errors'),
   path('data-errors', viewcustom.data_errors_page, name='data-errors'),
   path('show-tags', viewcustom.show_tags, name='show-tags'),
   path('show-yt-props', viewcustom.show_youtube_link_props, name='show-youtube-link-props'),
   path('write-bookmarks', viewcustom.write_bookmarks, name='write-bookmarks'),

   # login
   path('accounts/', include('django.contrib.auth.urls')),
   #path('logoutuser/', auth.LogoutView.as_view(), name ='logoutuser'),
   path('rsshistory/accounts/logout/', RedirectView.as_view(url='rsshistory/')),
   path('accounts/logout/', RedirectView.as_view(url='rsshistory/')),
]
