
from django.urls import path
from django.urls import include
from django.contrib.auth import views as auth
from django.views.generic import RedirectView
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
   path('refreshsource/<int:pk>/', views.refresh_source, name='refreshsource'),
   path('exportsources/', views.export_sources, name='exportsources'),

   path('entries/', views.RssEntriesListView.as_view(), name='entries'),
   path('entry/<int:pk>/', views.RssEntryDetailView.as_view(), name='entry-detail'),
   path('addentry', views.add_entry, name='addentry'),
   path('editentry/<int:pk>/', views.edit_entry, name='editentry'),
   path('removeentry/<int:pk>/', views.remove_entry, name='removeentry'),
   path('hideentry/<int:pk>/', views.hide_entry, name='hideentry'),
   path('persistent/<int:pk>/', views.make_persistent_entry, name='makeentrypersistent'),
   path('notpersistent/<int:pk>/', views.make_not_persistent_entry, name='makeentrynotpersistent'),
   path('importentries', views.import_entries, name='importentries'),
   path('exportentries/', views.export_entries, name='exportentries'),
   path('tagentry/<int:pk>/', views.tag_entry, name='tagentry'),

   path('configuration/', views.configuration, name='configuration'),

   path('searchinitview', views.search_init_view, name='searchinitview'),
   path('importview', views.import_view, name='importview'),

   path('accounts/', include('django.contrib.auth.urls')),
   #path('logoutuser/', auth.LogoutView.as_view(), name ='logoutuser'),
   path('rsshistory/accounts/logout/', RedirectView.as_view(url='rsshistory/')),
   path('accounts/logout/', RedirectView.as_view(url='rsshistory/')),
]
