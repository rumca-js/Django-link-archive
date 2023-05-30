from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from django.db.models.query import QuerySet
from django.db.models.query import EmptyQuerySet

from .models import SourceDataModel, LinkDataModel, ConfigurationEntry, UserConfig
from .forms import SourceForm, EntryForm, ConfigForm, EntryChoiceForm, ImportEntriesForm
from .basictypes import *
from .prjconfig import Configuration


# https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
app_name = Path("rsshistory")


def init_context(request, context):
    context['page_title'] = "Link Archive"
    context["django_app"] = str(app_name)
    context["base_generic"] = str(app_name / "base_generic.html")
    context["icon_size"] = "30px"

    c = Configuration.get_object(str(app_name))
    context['app_version'] = c.version

    users = UserConfig.objects.filter(user = request.user.get_username())
    if len(users) > 0:
       context['user_config'] = users[0]
    else:
       context['user_config'] = UserConfig()

    return context

def get_context(request = None):
    context = {}
    context = init_context(request, context)
    return context


def index(request):
    # Generate counts of some of the main objects
    num_sources = SourceDataModel.objects.all().count()
    num_entries = LinkDataModel.objects.all().count()
    num_persistent = LinkDataModel.objects.filter(persistent = True).count()

    context = get_context(request)

    context['num_sources'] = num_sources
    context['num_entries'] = num_entries
    context['num_persistent'] = num_persistent

    # Render the HTML template index.html with the data in the context variable
    return render(request, app_name / 'index.html', context=context)


def untagged_bookmarks(request):
    context = get_context(request)
    context['page_title'] += " - not tagged entries"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    links = LinkDataModel.objects.filter(tags__tag__isnull = True)
    context['links'] = links

    return render(request, app_name / 'entries_untagged.html', context)

