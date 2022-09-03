from django.shortcuts import render
from django.views import generic

from django.db.models.query import QuerySet
from django.db.models.query import EmptyQuerySet

from .models import RssLinkDataModel, RssLinkEntryDataModel, LinksData, LinkData
from .forms import NewLinkForm, ImportLinksForm, SourcesChoiceForm, EntryChoiceForm
from .basictypes import *
from pathlib import Path
from .prjconfig import Configuration


# https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
app_dir = Path("rsshistory")


def init_context(context):
    context['page_title'] = "RSS history index"
    context["django_app"] = str(app_dir)
    context["base_generic"] = str(app_dir / "base_generic.html")

    c = Configuration.get_object()

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
    context['version'] = c.version

    # Render the HTML template index.html with the data in the context variable
    return render(request, app_dir / 'index.html', context=context)


class RssLinkListView(generic.ListView):
    model = RssLinkDataModel
    context_object_name = 'link_list'
    paginate_by = 100

    def get_queryset(self):
        parameter_map = self.get_filters()
        self._tmp = RssLinkDataModel.objects.filter(**parameter_map)

        return self._tmp

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssLinkListView, self).get_context_data(**kwargs)
        context = init_context(context)
        # Create any data and add it to the context

        categories = self.get_request_values('category')
        subcategories = self.get_request_values('subcategory')
        title = self.get_request_values('title')

        categories = self.to_dict(categories)
        subcategories = self.to_dict(subcategories)
        title = self.to_dict(title)

        category_form = SourcesChoiceForm(categories = categories,
                                   subcategories = subcategories,
                                   title = title,
                                   filters = self.get_filters())

        context['category_form'] = category_form
        context['page_title'] = "News link list"

        return context

    def get_request_values(self, field):
        values = set()
        values.add("Any")

        for val in self._tmp.values(field):
            if str(val).strip() != "":
                values.add(val[field])
        return values

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
            if item.strip() != "":
                result.append((item, item))
        return result

    def get_filters(self):
        parameter_map = {}

        category = self.request.GET.get("category")
        if category and category != "Any":
           parameter_map['category'] = category

        subcategory = self.request.GET.get("subcategory")
        if subcategory and subcategory != "Any":
           parameter_map['subcategory'] = subcategory

        title = self.request.GET.get("title")
        if title and title != "Any":
           parameter_map['title'] = title

        return parameter_map


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



def export_data(request):
    context = get_context(request)
    context['page_title'] = "Export data"
    summary_text = ""

    links = RssLinkDataModel.objects.all()
    for link in links:
        data = LinkData.to_string(link)
        summary_text += data + "\n"

    context["summary_text"] = summary_text

    return render(request, app_dir / 'summary_present.html', context)



def configuration(request):
    context = get_context(request)
    context['page_title'] = "Configuration"
    
    c = Configuration.get_object()
    context['directory'] = c.directory
    context['version'] = c.version
    context['database_size_bytes'] = get_directory_size_bytes(c.directory)
    context['database_size_kbytes'] = get_directory_size_bytes(c.directory)/1024
    context['database_size_mbytes'] = get_directory_size_bytes(c.directory)/1024/1024

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
    paginate_by = 1000

    def get_queryset(self):
        parameter_map = self.get_filters()

        objs = RssLinkDataModel.objects.filter(**parameter_map)
        if objs.exists():
            index = 0
            for obj in objs:
                if index == 0:
                    self._tmp = RssLinkEntryDataModel.objects.filter(url = obj.url)
                else:
                    self._tmp = self._tmp | RssLinkEntryDataModel.objects.filter(url = obj.url)
                index += 1

            #self._tmp = RssLinkEntryDataModel.objects.filter(**parameter_map)
        else:
            self._tmp = RssLinkEntryDataModel.objects.all()

        return self._tmp

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssEntriesListView, self).get_context_data(**kwargs)
        context = init_context(context)
        # Create any data and add it to the context

        categories = self.get_request_values('category')
        subcategories = self.get_request_values('subcategory')
        title = self.get_request_values('title')

        categories = self.to_dict(categories)
        subcategories = self.to_dict(subcategories)
        title = self.to_dict(title)

        category_form = EntryChoiceForm(
                categories = categories,
                subcategories = subcategories,
                title = title,
                filters = self.get_filters())

        context['category_form'] = category_form
        context['page_title'] = "News link list"

        return context

    def get_request_values(self, field):
        values = set()

        parameter_map = self.get_filters()

        values.add("Any")
        for val in RssLinkDataModel.objects.filter(**parameter_map).values(field):
            if str(val).strip() != "":
                values.add(val[field])

        return values

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
            if item.strip() != "":
                result.append((item, item))
        return result

    def get_filters(self):
        parameter_map = {}

        category = self.request.GET.get("category")
        if category and category != "Any":
           parameter_map['category'] = category

        subcategory = self.request.GET.get("subcategory")
        if subcategory and subcategory != "Any":
           parameter_map['subcategory'] = subcategory

        title = self.request.GET.get("title")
        if title and title != "Any":
           parameter_map['title'] = title

        return parameter_map


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
