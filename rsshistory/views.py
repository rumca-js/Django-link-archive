from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from django.db.models.query import QuerySet
from django.db.models.query import EmptyQuerySet

from .models import RssLinkDataModel, RssLinkEntryDataModel, SourcesConverter, EntriesConverter
from .models import ConfigurationEntry

from .forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, EntryChoiceForm, ConfigForm
from .basictypes import *

from .prjconfig import Configuration


# https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
app_name = Path("rsshistory")


def init_context(context):
    context['page_title'] = "RSS history index"
    context["django_app"] = str(app_name)
    context["base_generic"] = str(app_name / "base_generic.html")

    c = Configuration.get_object()
    context['app_version'] = c.version

    return context

def get_context(request = None):
    context = {}
    context = init_context(context)
    return context


def index(request):
    c = Configuration.get_object()

    # Generate counts of some of the main objects
    num_sources = RssLinkDataModel.objects.all().count()
    num_entries = RssLinkEntryDataModel.objects.all().count()
    num_favourites = RssLinkEntryDataModel.objects.filter(favourite = True).count()

    context = get_context(request)

    context['num_sources'] = num_sources
    context['num_entries'] = num_entries
    context['num_favourites'] = num_favourites

    # Render the HTML template index.html with the data in the context variable
    return render(request, app_name / 'index.html', context=context)


class RssSourceListView(generic.ListView):
    model = RssLinkDataModel
    context_object_name = 'source_list'
    paginate_by = 100

    def get_queryset(self):

        self.filter_form = SourcesChoiceForm(args = self.request.GET)
        return self.filter_form.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssSourceListView, self).get_context_data(**kwargs)
        context = init_context(context)
        # Create any data and add it to the context

        self.filter_form.create()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse('rsshistory:sources')

        context['filter_form'] = self.filter_form
        context['page_title'] += " - news source list"

        return context


class RssSourceDetailView(generic.DetailView):
    model = RssLinkDataModel

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssSourceDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        c = Configuration.get_object()
        c.download_rss(self.object)

        context['page_title'] += " - " + self.object.title

        return context


def add_source(request):
    context = get_context(request)
    context['page_title'] += " - add source"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = SourceForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            valid = True
            form.save()

        context['form'] = form

        return render(request, app_name / 'form_basic.html', context)

        #    # process the data in form.cleaned_data as required
        #    # ...
        #    # redirect to a new URL:
        #    #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = SourceForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:addsource')
        context['form'] = form

    return render(request, app_name / 'form_basic.html', context)


def edit_source(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit source"
    context['pk'] = pk

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssLinkDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, app_name / 'source_edit_does_not_exist.html', context)

    ob = ft[0]

    if request.method == 'POST':
        form = SourceForm(request.POST, instance=ob[0])
        context['form'] = form

        if form.is_valid():
            form.save()

            context['source'] = ft[0]
            return render(request, app_name / 'source_edit_ok.html', context)

        context['summary_text'] = "Could not edit source"

        return render(request, app_name / 'summary_present', context)
    else:
        form = SourceForm(init_obj=obj)
        form.method = "POST"
        form.action_url = reverse('rsshistory:editsource', args=[pk])
        context['form'] = form
        return render(request, app_name / 'form_basic.html', context)


def import_sources(request):
    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import sources"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportSourcesForm(request.POST)

        if form.is_valid():
            for source in form.get_sources():

                if RssLinkDataModel.objects.filter(url=source.url).exists():
                    summary_text += source.title + " " + source.url + " " + " Error: Already present in db\n"
                else:
                    record = RssLinkDataModel(url=source.url,
                                                title=source.title,
                                                category=source.category,
                                                subcategory=source.subcategory)
                    record.save()
                    summary_text += source.title + " " + source.url + " " + " OK\n"
        else:
            summary_text = "Form is invalid"

        context["form"] = form
        context['summary_text'] = summary_text
        return render(request, app_name / 'sources_import_summary.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ImportSourcesForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:importsources')
        context["form"] = form
        return render(request, app_name / 'form_basic.html', context)


def import_entries(request):
    # TODO
    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import entries"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportEntriesForm(request.POST)

        if form.is_valid():
            summary_text = "Import entries log\n"

            for entry in form.get_entries():

                if RssLinkEntryDataModel.objects.filter(url=entry.url).exists():
                    summary_text += entry.title + " " + entry.url + " " + " Error: Already present in db\n"
                else:
                    try:
                        record = RssLinkEntryDataModel(url=entry.url,
                                                    title=entry.title,
                                                    description=entry.description,
                                                    link=entry.link,
                                                    date_published=entry.date_published,
                                                    favourite = entry.favourite)
                        record.save()
                        summary_text += entry.title + " " + entry.url + " " + " OK\n"
                    except Exception as e:
                        summary_text += entry.title + " " + entry.url + " " + " NOK\n"
        else:
            summary_text = "Form is invalid"

        context["form"] = form
        context['summary_text'] = summary_text
        return render(request, app_name / 'entries_import_summary.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ImportEntriesForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:importentries')
        context["form"] = form
        return render(request, app_name / 'form_basic.html', context)


def remove_source(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove source"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssLinkDataModel.objects.filter(id=pk)
    if ft.exists():
        entries = RssLinkEntryDataModel.objects.filter(url = ft[0].url)
        if entries.exists():
            entries.delete()

        ft.delete()
        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return render(request, app_name / 'summary_present.html', context)


def remove_all_sources(request):
    context = get_context(request)
    context['page_title'] += " - remove all links"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssLinkDataModel.objects.all()
    if ft.exists():
        ft.delete()
        context["summary_text"] = "Removing all sources ok"
    else:
        context["summary_text"] = "No source to remove"

    return render(request, app_name / 'summary_present.html', context)



def export_sources(request):
    context = get_context(request)
    context['page_title'] += " - export data"
    summary_text = ""

    sources = RssLinkDataModel.objects.all()

    s_converter = SourcesConverter()
    s_converter.set_sources(sources)

    context["summary_text"] = s_converter.get_text()

    return render(request, app_name / 'summary_present.html', context)


def export_entries(request):
    context = get_context(request)
    context['page_title'] += " - export data"
    summary_text = ""

    entries = RssLinkEntryDataModel.objects.filter(favourite = True)

    c = Configuration.get_object()
    c.export_entries(entries, 'favourite')

    context["summary_text"] = "Exported entries"

    return render(request, app_name / 'summary_present.html', context)



def configuration(request):
    context = get_context(request)
    context['page_title'] += " - Configuration"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)
    
    c = Configuration.get_object()
    context['directory'] = c.directory
    context['database_size_bytes'] = get_directory_size_bytes(c.directory)
    context['database_size_kbytes'] = get_directory_size_bytes(c.directory)/1024
    context['database_size_mbytes'] = get_directory_size_bytes(c.directory)/1024/1024

    threads = c.get_threads()
    for thread in threads:
        items = thread.get_processs_list()

    context['thread_list'] = threads
    
    if c.server_log_file.exists():
        with open(c.server_log_file.resolve(), "r") as fh:
             context['server_log_data'] = fh.read()
             
    context['server_path'] = Path(".").resolve()
    context['directory'] = Path(".").resolve()

    ob = ConfigurationEntry.objects.all()
    if not ob.exists():
        rec = ConfigurationEntry()
        rec.save()

    ob = ConfigurationEntry.objects.all()

    if request.method == 'POST':
        form = ConfigForm(request.POST, instance=ob[0])
        if form.is_valid():
            form.save()

        ob = ConfigurationEntry.objects.all()
    
    form = ConfigForm(instance = ob[0])
    form.method = "POST"
    form.action_url = reverse('rsshistory:configuration')

    context['config_form'] = form

    return render(request, app_name / 'configuration.html', context)


class RssEntriesListView(generic.ListView):
    model = RssLinkEntryDataModel
    context_object_name = 'entries_list'
    paginate_by = 500

    def get_queryset(self):
        self.filter_form = EntryChoiceForm(args = self.request.GET)
        return self.filter_form.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssEntriesListView, self).get_context_data(**kwargs)
        context = init_context(context)
        # Create any data and add it to the context

        self.filter_form.create()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse('rsshistory:entries')

        context['filter_form'] = self.filter_form
        context['page_title'] += " - entries"

        return context


class RssEntryDetailView(generic.DetailView):
    model = RssLinkEntryDataModel

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssEntryDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        context['page_title'] += " - " + self.object.title

        return context


def favourite_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - favourite entry"
    context['pk'] = pk

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssLinkEntryDataModel.objects.get(id=pk)
    fav = ft.favourite
    ft.favourite = not ft.favourite
    ft.save()

    summary_text = "Link changed to state: " + str(ft.favourite)

    context["summary_text"] = summary_text

    return render(request, app_name / 'summary_present.html', context)


def add_entry(request):
    context = get_context(request)
    context['page_title'] += " - Add entry"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = EntryForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            valid = True
            form.save()

        context['form'] = form

        return render(request, app_name / 'form_basic.html', context)

        #    # process the data in form.cleaned_data as required
        #    # ...
        #    # redirect to a new URL:
        #    #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = EntryForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:addentry')
        context['form'] = form

    return render(request, app_name / 'form_basic.html', context)


def edit_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit entry"
    context['pk'] = pk

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    ob = RssLinkEntryDataModel.objects.filter(id=pk)
    if not ob.exists():
       return render(request, app_name / 'entry_edit_exists.html', context)

    if request.method == 'POST':
        form = EntryForm(request.POST, instance=ob[0])
        context['form'] = form

        if form.is_valid():
            form.save()

            context['entry'] = ob[0]
            return render(request, app_name / 'entry_edit_ok.html', context)

        context['summary_text'] = "Could not edit entry"

        return render(request, app_name / 'summary_present', context)
    else:
        form = EntryForm(instance=ob[0])
        form.method = "POST"
        form.action_url = reverse('rsshistory:editentry', args=[pk])
        context['form'] = form
        return render(request, app_name / 'form_basic.html', context)


def remove_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove entry"

    if not request.user.is_authenticated:
        return render(request, app_name / 'missing_rights.html', context)

    entries = RssLinkEntryDataModel.objects.filter(url = ft[0].url)
    if entries.exists():
        entries.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return render(request, app_name / 'summary_present.html', context)
