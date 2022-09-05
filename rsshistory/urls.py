
from django.urls import path
from . import views

app_name = 'rsshistory'

urlpatterns = [
   path('', views.index, name='index'),
   path('links/', views.RssLinkListView.as_view(), name='links'),
   path('link/<int:pk>/', views.RssLinkDetailView.as_view(), name='link-detail'),
   path('addlink', views.add_link, name='addlink'),
   path('importlinks', views.import_links, name='importlinks'),
   path('removelink/<int:pk>/', views.remove_link, name='removelink'),
   path('removealllinks/', views.remove_all_links, name='removealllinks'),
   path('editlink/<int:pk>/', views.edit_link, name='editlink'),

   path('entries/', views.RssEntriesListView.as_view(), name='entries'),
   path('entry/<int:pk>/', views.RssEntryDetailView.as_view(), name='entry-detail'),
   path('favourite/<int:pk>/', views.favourite_entry, name='entryfavourite'),

   path('exportsources/', views.export_sources, name='exportsources'),
   path('exportentries/', views.export_entries, name='exportentries'),
   path('configuration/', views.configuration, name='configuration'),
]
