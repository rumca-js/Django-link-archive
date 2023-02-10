
from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth
from django.views.generic import RedirectView
from . import views

app_name = str(views.app_name)

urlpatterns = [
   path('', views.index, name='index'),

   # sources
   path('sources/', views.RssSourceListView.as_view(), name='sources'),
   path('source/<int:pk>/', views.RssSourceDetailView.as_view(), name='source-detail'),
   path('source-add', views.add_source, name='source-add'),
   path('source-remove/<int:pk>/', views.remove_source, name='source-remove'),
   path('source-edit/<int:pk>/', views.edit_source, name='source-edit'),
   path('source-refresh/<int:pk>/', views.refresh_source, name='source-refresh'),
   path('sources-remove-all/', views.remove_all_sources, name='sources-remove-all'),
   path('sources-import', views.import_sources, name='sources-import'),
   path('sources-export/', views.export_sources, name='sources-export'),
   path('source-wayback-save/<int:pk>/', views.wayback_save, name='source-wayback-save'),

   # entries
   path('entries/', views.RssEntriesListView.as_view(), name='entries'),
   path('entry/<int:pk>/', views.RssEntryDetailView.as_view(), name='entry-detail'),
   path('entry-add', views.add_entry, name='entry-add'),
   path('entry-edit/<int:pk>/', views.edit_entry, name='entry-edit'),
   path('entry-remove/<int:pk>/', views.remove_entry, name='entry-remove'),
   path('entry-hide/<int:pk>/', views.hide_entry, name='entry-hide'),
   path('entry-star/<int:pk>/', views.make_persistent_entry, name='entry-star'),
   path('entry-notstar/<int:pk>/', views.make_not_persistent_entry, name='entry-notstar'),
   path('entry-tag/<int:pk>/', views.tag_entry, name='entry-tag'),
   path('entries-import', views.import_entries, name='entries-import'),
   path('entries-untagged/', views.NotBookmarkedView.as_view(), name='entries-untagged'),

   # comment
   path('entry-comment-add/<int:link_id>', views.entry_add_comment, name='entry-comment-add'),
   path('entry-comment-edit/<int:pk>/', views.entry_comment_edit, name='entry-comment-edit'),
   path('entry-comment-remove/<int:pk>/', views.entry_comment_remove, name='entry-comment-remove'),

   # custom views
   path('configuration/', views.configuration, name='configuration'),
   path('system-status/', views.system_status, name='system-status'),
   path('searchinitview', views.search_init_view, name='searchinitview'),
   path('import-view', views.import_view, name='import-view'),
   path('import-source-ia/<int:pk>/', views.import_source_from_ia, name='import-source-ia'),
   path('truncate-errors', views.truncate_errors, name='truncate-errors'),
   path('data-errors', views.show_errors_page, name='data-errors'),
   path('show-tags', views.show_tags, name='show-tags'),
   path('write-bookmarks', views.write_bookmarks, name='write-bookmarks'),

   # login
   path('accounts/', include('django.contrib.auth.urls')),
   #path('logoutuser/', auth.LogoutView.as_view(), name ='logoutuser'),
   path('rsshistory/accounts/logout/', RedirectView.as_view(url='rsshistory/')),
   path('accounts/logout/', RedirectView.as_view(url='rsshistory/')),
]
