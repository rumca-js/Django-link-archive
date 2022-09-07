from pathlib import Path

from django.shortcuts import render
from django.views import generic

from django.db.models.query import QuerySet
from django.db.models.query import EmptyQuerySet

from .models import RssLinkDataModel, RssLinkEntryDataModel, SourcesConverter, EntriesConverter
from .models import ConfigurationEntry

from .forms import NewLinkForm, ImportLinksForm, SourcesChoiceForm, EntryChoiceForm, ConfigForm
from .basictypes import *

from .prjconfig import Configuration


# https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
app_dir = Path("rsshistory")


def init_context(context):
    context['page_title'] = "RSS history index"
    context["django_app"] = str(app_dir)
    context["base_generic"] = str(app_dir / "base_generic.html")

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
    num_links = RssLinkDataModel.objects.all().count()
    num_entries = RssLinkEntryDataModel.objects.all().count()

    context = get_context(request)

    context['num_links'] = num_links
    context['num_entries'] = num_entries

    # Render the HTML template index.html with the data in the context variable
    return render(request, app_dir / 'index.html', context=context)


class RssLinkListView(generic.ListView):
    model = RssLinkDataModel
    context_object_name = 'link_list'
    paginate_by = 100

    def get_queryset(self):

        self.filter_form = SourcesChoiceForm(args = self.request.GET)
        return self.filter_form.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssLinkListView, self).get_context_data(**kwargs)
        context = init_context(context)
        # Create any data and add it to the context

        self.filter_form.create()

        context['filter_form'] = self.filter_form
        context['page_title'] = "News link list"

        return context


class RssLinkDetailView(generic.DetailView):
    model = RssLinkDataModel

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssLinkDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        c = Configuration.get_object()
        c.download_rss(self.object)

        context['page_title'] = self.object.title

        return context


def add_link(request):
    context = get_context(request)
    context['page_title'] = "Add link"

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = NewLinkForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            model = form.to_model()

            ft = RssLinkDataModel.objects.filter(url=model.url)
            if ft.exists():
                context['form'] = form
                context['link'] = ft[0]
                return render(request, app_dir / 'add_link_exists.html', context)
            else:
                model.save()

                context['form'] = form
                context['link'] = model
                return render(request, app_dir / 'add_link_added.html', context)
        #    # process the data in form.cleaned_data as required
        #    # ...
        #    # redirect to a new URL:
        #    #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = NewLinkForm()
        context['form'] = form

    return render(request, app_dir / 'add_link.html', context)


def import_links(request):
    summary_text = ""
    context = get_context(request)
    context['page_title'] = "Import links"

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportLinksForm(request.POST)

        if form.is_valid():
            rawlinks = form.cleaned_data['rawlinks']
            links = LinksData(rawlinks)
            for link in links.links:

                if RssLinkDataModel.objects.filter(url=link.url).exists():
                    summary_text += link.title + " " + link.url + " " + " Error: Already present in db\n"
                else:
                    record = RssLinkDataModel(url=link.url,
                                                title=link.title,
                                                category=link.category,
                                                subcategory=link.subcategory)
                    record.save()
                    summary_text += link.title + " " + link.url + " " + " OK\n"

        context["form"] = form
        context['summary_text'] = summary_text
        return render(request, app_dir / 'import_links_summary.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ImportLinksForm()
        context["form"] = form
        context['page_title'] = "Import links"
        return render(request, app_dir / 'import_links.html', context)


def remove_link(request, pk):
    context = get_context(request)
    context['page_title'] = "Remove link"

    ft = RssLinkDataModel.objects.filter(id=pk)
    if ft.exists():
        entries = RssLinkEntryDataModel.objects.filter(url = ft[0].url)
        if entries.exists():
            entries.delete()

        ft.delete()
        return render(request, app_dir / 'remove_link_ok.html', context)
    else:
        return render(request, app_dir / 'remove_link_nok.html', context)


def remove_all_links(request):
    context = get_context(request)
    context['page_title'] = "Remove all links"

    ft = RssLinkDataModel.objects.all()
    if ft.exists():
        ft.delete()
        return render(request, app_dir / 'remove_all_links_ok.html', context)
    else:
        return render(request, app_dir / 'remove_all_links_nok.html', context)



def export_sources(request):
    context = get_context(request)
    context['page_title'] = "Export data"
    summary_text = ""

    sources = RssLinkDataModel.objects.all()

    s_converter = SourcesConverter()
    s_converter.set_sources(sources)

    context["summary_text"] = s_converter.get_text()

    return render(request, app_dir / 'summary_present.html', context)


def export_entries(request):
    context = get_context(request)
    context['page_title'] = "Export data"
    summary_text = ""

    entries = RssLinkEntryDataModel.objects.all()

    c = Configuration.get_object()
    c.export_entries(entries)

    context["summary_text"] = "Exported entries"

    return render(request, app_dir / 'summary_present.html', context)



def configuration(request):
    context = get_context(request)
    context['page_title'] = "Configuration"
    
    c = Configuration.get_object()
    context['directory'] = c.directory
    context['database_size_bytes'] = get_directory_size_bytes(c.directory)
    context['database_size_kbytes'] = get_directory_size_bytes(c.directory)/1024
    context['database_size_mbytes'] = get_directory_size_bytes(c.directory)/1024/1024

    ob = ConfigurationEntry.objects.all()
    if not ob.exists():
        rec = ConfigurationEntry(git_path = ".",
                                 git_repo = "TODO",
                                 git_user = "TODO",
                                 git_token = "TODO")
        rec.save()

    ob = ConfigurationEntry.objects.all()

    if request.method == 'POST':
        form = ConfigForm(request.POST, instance=ob[0])
        if form.is_valid():
            form.save()

        ob = ConfigurationEntry.objects.all()
        context['config_form'] = ConfigForm(instance = ob[0])
    else:
        context['config_form'] = ConfigForm(instance = ob[0])

    return render(request, app_dir / 'configuration.html', context)


def edit_link(request, pk):
    context = get_context(request)
    context['page_title'] = "Edit link"
    context['pk'] = pk

    ft = RssLinkDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, app_dir / 'edit_link_does_not_exist.html', context)

    obj = ft[0]

    if request.method == 'POST':
        form = NewLinkForm(request.POST)
        context['form'] = form

        if form.is_valid():
            model = form.to_model()

            ft = RssLinkDataModel.objects.filter(url=model.url)
            if ft.exists():
                ft.delete()
                model.save()

                context['link'] = ft[0]
                return render(request, app_dir / 'edit_link_ok.html', context)
            else:
                model.save()
                return render(request, app_dir / 'edit_link_does_not_exist.html', context)

        context['summary_text'] = "Could not edit link"

        return render(request, app_dir / 'summary_present', context)
    else:
        form = NewLinkForm(init_obj=obj)
        context['form'] = form
        return render(request, app_dir / 'edit_link.html', context)


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

        context['filter_form'] = self.filter_form
        context['page_title'] = "News link list"

        return context


class RssEntryDetailView(generic.DetailView):
    model = RssLinkEntryDataModel

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssEntryDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        context['page_title'] = self.object.title

        return context


def favourite_entry(request, pk):
    context = get_context(request)
    context['page_title'] = "Favourite entry"
    context['pk'] = pk

    ft = RssLinkEntryDataModel.objects.get(id=pk)
    fav = ft.favourite
    ft.favourite = not ft.favourite
    ft.save()

    summary_text = "Link changed to state: " + str(ft.favourite)

    context["summary_text"] = summary_text

    return render(request, app_dir / 'summary_present.html', context)

