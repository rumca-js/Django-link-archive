
from django.urls import path
from . import views

app_name = str(views.app_name)

urlpatterns = [
   path('', views.index, name='index'),
   path('sources/', views.RssSourceListView.as_view(), name='sources'),
   path('source/<int:pk>/', views.RssSourceDetailView.as_view(), name='source-detail'),
   path('addsource', views.add_source, name='addsource'),
   path('importsources', views.import_sources, name='importsources'),
   path('removesource/<int:pk>/', views.remove_source, name='removesource'),
   path('removeallsources/', views.remove_all_sources, name='removeallsources'),
   path('editsource/<int:pk>/', views.edit_source, name='editsource'),
   path('exportsources/', views.export_sources, name='exportsources'),

   path('entries/', views.RssEntriesListView.as_view(), name='entries'),
   path('entry/<int:pk>/', views.RssEntryDetailView.as_view(), name='entry-detail'),
   path('addentry', views.add_entry, name='addentry'),
   path('editentry/<int:pk>/', views.edit_entry, name='editentry'),
   path('removeentry/<int:pk>/', views.remove_entry, name='removeentry'),
   path('hideentry/<int:pk>/', views.hide_entry, name='hideentry'),
   path('persistent/<int:pk>/', views.persistent_entry, name='entrypersistent'),
   path('importentries', views.import_entries, name='importentries'),
   path('exportentries/', views.export_entries, name='exportentries'),

   path('configuration/', views.configuration, name='configuration'),
]
