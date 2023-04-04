from pathlib import Path
from datetime import datetime, date, timedelta
import traceback

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from django.db.models.query import QuerySet
from django.db.models.query import EmptyQuerySet

from .models import RssSourceDataModel, RssSourceEntryDataModel, ConfigurationEntry
from .models import RssSourceImportHistory, RssSourceExportHistory
from .serializers.converters import ModelCollectionConverter, CsvConverter

from .forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, ConfigForm, CommentEntryForm
from .basictypes import *

from .prjconfig import Configuration


# https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
app_name = Path("rsshistory")


def init_context(context):
    context['page_title'] = "RSS archive"
    context["django_app"] = str(app_name)
    context["base_generic"] = str(app_name / "base_generic.html")

    c = Configuration.get_object(str(app_name))
    context['app_version'] = c.version

    return context

def get_context(request = None):
    context = {}
    context = init_context(context)
    return context


def index(request):
    c = Configuration.get_object(str(app_name))

    # Generate counts of some of the main objects
    num_sources = RssSourceDataModel.objects.all().count()
    num_entries = RssSourceEntryDataModel.objects.all().count()
    num_persistent = RssSourceEntryDataModel.objects.filter(persistent = True).count()

    context = get_context(request)

    context['num_sources'] = num_sources
    context['num_entries'] = num_entries
    context['num_persistent'] = num_persistent

    # Render the HTML template index.html with the data in the context variable
    return render(request, app_name / 'index.html', context=context)


def untagged_bookmarks(request):
    context = get_context(request)
    context['page_title'] += " - Find not tagged entries"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    links = RssSourceEntryDataModel.objects.filter(tags__tag__isnull = True)
    context['links'] = links

    return render(request, app_name / 'entries_untagged.html', context)


from .models import RssEntryCommentDataModel

def entry_add_comment(request, link_id):
    context = get_context(request)
    context['page_title'] += " - Add comment"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    print("Link id" + str(link_id))
    link = RssSourceEntryDataModel.objects.get(id = link_id)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = CommentEntryForm(request.POST)
        if form.is_valid():
            form.save_comment()

            context["summary_text"] = "Added a new comment"
            return render(request, app_name / 'summary_present.html', context)

        context["summary_text"] = "Could not add a comment"

        return render(request, app_name / 'summary_present.html', context)

    else:
        author = request.user.username
        form = CommentEntryForm(initial={'author' : author, 'link' : link.link})

    form.method = "POST"
    form.pk = link_id
    form.action_url = reverse('rsshistory:entry-comment-add', args=[link_id])

    context['form'] = form
    context['form_title'] = link.title
    context['form_description'] = link.title

    return render(request, app_name / 'form_basic.html', context)


def entry_comment_edit(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit comment"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    comment_obj = RssEntryCommentDataModel.objects.get(id = pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        context["summary_text"] = "You are not the author!"
        return render(request, app_name / 'summary_present.html', context)

    if request.method == 'POST':
        form = CommentEntryForm(request.POST)

        if form.is_valid():
            comment_obj.comment = form.cleaned_data['comment']
            comment_obj.save()

            context["summary_text"] = "Comment edited"

            return render(request, app_name / 'summary_present.html', context)
        else:
            context["summary_text"] = "Form is not valid"

            return render(request, app_name / 'summary_present.html', context)
    else:
        form = CommentEntryForm(instance = comment_obj)
        form.method = "POST"
        form.pk = pk
        form.action_url = reverse('rsshistory:entry-comment-edit', args=[pk])

        context['form'] = form
        context['form_title'] = link.title
        context['form_description'] = link.title

        return render(request, app_name / 'form_basic.html', context)


def entry_comment_remove(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove comment"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    comment_obj = RssEntryCommentDataModel.objects.get(id = pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        context["summary_text"] = "You are not the author!"
        return render(request, app_name / 'summary_present.html', context)

    comment_obj.delete()

    context["summary_text"] = "Removed comment"

    return render(request, app_name / 'summary_present.html', context)



