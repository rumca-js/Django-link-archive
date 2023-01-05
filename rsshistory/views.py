from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from django.db.models.query import QuerySet
from django.db.models.query import EmptyQuerySet

from .models import RssSourceDataModel, RssSourceEntryDataModel, RssEntryTagsDataModel, ConfigurationEntry
from .converters import SourcesConverter, EntriesConverter

from .forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, EntryChoiceForm, ConfigForm
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


class RssSourceListView(generic.ListView):
    model = RssSourceDataModel
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
    model = RssSourceDataModel

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssSourceDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        c = Configuration.get_object(str(app_name))
        c.download_rss(self.object)

        context['page_title'] += " - " + self.object.title

        return context


def add_source(request):
    context = get_context(request)
    context['page_title'] += " - add source"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = SourceForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            form.save()

            context["summary_text"] = "Source added"
            return render(request, app_name / 'summary_present.html', context)
        else:
            context["summary_text"] = "Source not added"
            return render(request, app_name / 'summary_present.html', context)

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

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssSourceDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, app_name / 'source_edit_does_not_exist.html', context)

    ob = ft[0]

    if request.method == 'POST':
        form = SourceForm(request.POST, instance=ob)
        context['form'] = form

        if form.is_valid():
            form.save()

            context['source'] = ob
            return render(request, app_name / 'source_edit_ok.html', context)

        context['summary_text'] = "Could not edit source"

        return render(request, app_name / 'summary_present.html', context)
    else:
        if not ob.favicon:
            from .webtools import Page
            p = Page(ob.url)

            form = SourceForm(instance=ob, initial={'favicon' : p.get_domain() +"/favicon.ico" })
        else:
            form = SourceForm(instance=ob)

        form.method = "POST"
        form.action_url = reverse('rsshistory:editsource', args=[pk])
        context['form'] = form
        return render(request, app_name / 'form_basic.html', context)


def refresh_source(request, pk):
    from .models import RssSourceOperationalData

    context = get_context(request)
    context['page_title'] += " - refresh source"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssSourceDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, app_name / 'source_edit_does_not_exist.html', context)

    ob = ft[0]

    operational = RssSourceOperationalData.objects.filter(url = ob.url)
    if operational.exists():
        print("saving")
        op = operational[0]
        op.date_fetched = None
        op.save()
    else:
        print("not saving")

    c = Configuration.get_object(str(app_name))
    c.download_rss(ob, True)

    context['summary_text'] = "Source added to refresh queue"

    return render(request, app_name / 'summary_present.html', context)


def import_sources(request):
    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import sources"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportSourcesForm(request.POST)

        if form.is_valid():
            for source in form.get_sources():

                if RssSourceDataModel.objects.filter(url=source.url).exists():
                    summary_text += source.title + " " + source.url + " " + " Error: Already present in db\n"
                else:
                    record = RssSourceDataModel(url=source.url,
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

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportEntriesForm(request.POST)

        if form.is_valid():
            summary_text = "Import entries log\n"

            for entry in form.get_entries():

                if RssSourceEntryDataModel.objects.filter(url=entry.url).exists():
                    summary_text += entry.title + " " + entry.url + " " + " Error: Already present in db\n"
                else:
                    try:
                        record = RssSourceEntryDataModel(url=entry.url,
                                                    title=entry.title,
                                                    description=entry.description,
                                                    link=entry.link,
                                                    date_published=entry.date_published,
                                                    persistent = entry.persistent)
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

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssSourceDataModel.objects.filter(id=pk)
    if ft.exists():
        source_url = ft[0].url
        ft.delete()
        
        # TODO checkbox - or other button to remove corresponding entries
        #entries = RssSourceEntryDataModel.objects.filter(url = source_url)
        #if entries.exists():
        #    entries.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return render(request, app_name / 'summary_present.html', context)


def remove_all_sources(request):
    context = get_context(request)
    context['page_title'] += " - remove all links"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssSourceDataModel.objects.all()
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

    sources = RssSourceDataModel.objects.all()

    s_converter = SourcesConverter()
    s_converter.set_sources(sources)

    context["summary_text"] = s_converter.get_text()

    return render(request, app_name / 'summary_present.html', context)


def export_entries(request):
    context = get_context(request)
    context['page_title'] += " - export data"
    summary_text = ""

    entries = RssSourceEntryDataModel.objects.filter(persistent = True)

    c = configuration.get_object(str(app_name))
    c.export_entries(entries, 'persistent')

    context["summary_text"] = "Exported entries"

    return render(request, app_name / 'summary_present.html', context)



def configuration(request):
    context = get_context(request)
    context['page_title'] += " - Configuration"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)
    
    c = Configuration.get_object(str(app_name))
    context['directory'] = c.directory
    context['database_size_bytes'] = get_directory_size_bytes(c.directory)
    context['database_size_kbytes'] = get_directory_size_bytes(c.directory)/1024
    context['database_size_mbytes'] = get_directory_size_bytes(c.directory)/1024/1024

    from .models import PersistentInfo
    context['log_items'] = PersistentInfo.objects.all()

    threads = c.get_threads()
    for thread in threads:
        items = thread.get_processs_list()

    context['thread_list'] = threads
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
    model = RssSourceEntryDataModel
    context_object_name = 'entries_list'
    paginate_by = 200

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

        c = Configuration.get_object(str(app_name))
        thread = c.get_threads()[0]
        queue_size = thread.get_queue_size()

        context['filter_form'] = self.filter_form
        context['page_title'] += " - entries"
        context['rss_are_fetched'] = queue_size > 0
        context['rss_queue_size'] = queue_size

        return context


class RssEntryDetailView(generic.DetailView):
    model = RssSourceEntryDataModel

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssEntryDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        if self.object.language == None:
            self.object.update_language()

        context['page_title'] += " - " + self.object.title
        context['tag_string'] = self.object.get_tag_string()

        return context


def make_persistent_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - persistent entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssSourceEntryDataModel.objects.get(id=pk)
    fav = ft.persistent
    ft.persistent = True
    ft.user = request.user.username
    ft.save()

    summary_text = "Link changed to state: " + str(ft.persistent)

    context["summary_text"] = summary_text

    return render(request, app_name / 'summary_present.html', context)


def make_not_persistent_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - persistent entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssSourceEntryDataModel.objects.get(id=pk)
    fav = ft.persistent
    ft.persistent = False
    ft.user = request.user.username
    ft.save()

    summary_text = "Link changed to state: " + str(ft.persistent)

    context["summary_text"] = summary_text

    return render(request, app_name / 'summary_present.html', context)


def add_entry(request):
    context = get_context(request)
    context['page_title'] += " - Add entry"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = EntryForm(request.POST)

        ob = RssSourceEntryDataModel.objects.filter(link=request.POST.get('link'))
        if ob.exists():
            context['form'] = form
            context['entry'] = ob[0]

            return render(request, app_name / 'entry_edit_exists.html', context)

        # check whether it's valid:
        if form.is_valid():
            form.save_form()

            context['form'] = form

            ob = RssSourceEntryDataModel.objects.filter(link=request.POST.get('link'))
            if ob.exists():
                context['entry'] = ob[0]

            return render(request, app_name / 'entry_added.html', context)

        context["summary_text"] = "Could not add link"
        return render(request, app_name / 'summary_present.html', context)

        #    # process the data in form.cleaned_data as required
        #    # ...
        #    # redirect to a new URL:
        #    #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        author = request.user.username
        form = EntryForm(initial={'user' : author})
        form.method = "POST"
        form.action_url = reverse('rsshistory:addentry')
        context['form'] = form

    return render(request, app_name / 'form_basic.html', context)


def edit_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit entry"

    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    obs = RssSourceEntryDataModel.objects.filter(id=pk)
    if not obs.exists():
        context['summary_text'] = "Such entry does not exist"
        return render(request, app_name / 'summary_present.html', context)

    ob = obs[0]
    if ob.user is None or ob.user == "":
        ob.user = str(request.user.username)
        ob.description = "test"
        ob.save()

    if request.method == 'POST':
        form = EntryForm(request.POST, instance=ob)
        context['form'] = form

        if form.is_valid():
            form.save()

            context['entry'] = ob
            return render(request, app_name / 'entry_edit_ok.html', context)

        context['summary_text'] = "Could not edit entry"

        return render(request, app_name / 'summary_present.html', context)
    else:
        form = EntryForm(instance=ob)
        #form.fields['user'].initial = request.user.username
        form.method = "POST"
        form.action_url = reverse('rsshistory:editentry', args=[pk])
        context['form'] = form
        return render(request, app_name / 'form_basic.html', context)


def remove_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove entry"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    entry = RssSourceEntryDataModel.objects.filter(id=pk)
    if entry.exists():
        entry.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return render(request, app_name / 'summary_present.html', context)


def hide_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - hide entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    objs = RssSourceEntryDataModel.objects.filter(id=pk)
    obj = objs[0]

    fav = obj.dead
    obj.dead = not obj.dead
    obj.save()

    summary_text = "Link changed to state: " + str(obj.dead)

    context["summary_text"] = summary_text

    return render(request, app_name / 'summary_present.html', context)


def tag_entry(request, pk):
    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/
    from .forms import TagEntryForm
    from .models import RssEntryTagsDataModel

    context = get_context(request)
    context['page_title'] += " - tag entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    objs = RssSourceEntryDataModel.objects.filter(id=pk)

    if not objs.exists():
        context["summary_text"] = "Sorry, such object does not exist"
        return render(request, app_name / 'summary_present.html', context)

    obj = objs[0]
    if not obj.persistent:
        context["summary_text"] = "Sorry, only persistent objects can be tagged"
        return render(request, app_name / 'summary_present.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = TagEntryForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            form.save_tags()

            context["summary_text"] = "Entry tagged"
            return render(request, app_name / 'summary_present.html', context)
        else:
            context["summary_text"] = "Entry not added"
            return render(request, app_name / 'summary_present.html', context)

        #    # process the data in form.cleaned_data as required
        #    # ...
        #    # redirect to a new URL:
        #    #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        author = request.user.username
        link = obj.link
        tag_string = RssEntryTagsDataModel.get_author_tag_string(author, link)

        if tag_string:
            form = TagEntryForm(initial={'link' : link, 'author' : author, 'tag' : tag_string})
        else:
            form = TagEntryForm(initial={'link' : link, 'author' : author})

        form.method = "POST"
        form.pk = pk
        form.action_url = reverse('rsshistory:tagentry', args=[pk])
        context['form'] = form
        context['form_title'] = obj.title
        context['form_description'] = obj.title

    return render(request, app_name / 'form_basic.html', context)


def search_init_view(request):
    from .models import RssEntryTagsDataModel
    from .forms import GoogleChoiceForm

    context = get_context(request)
    context['page_title'] += " - search view"

    filter_form = EntryChoiceForm(args = request.GET)
    filter_form.create()
    filter_form.method = "GET"
    filter_form.action_url = reverse('rsshistory:entries')

    context['form'] = filter_form

    return render(request, app_name / 'form_search.html', context)

def import_view(request):
    from .exporters.readinglist import ReadingList
    from .webtools import Page

    context = get_context(request)
    context['page_title'] += " - import view"

    c = Configuration.get_object(str(app_name))
    import_path = c.get_import_path() / 'readingList.csv'

    summary_text = ""

    rlist_data = import_path.read_text()

    rlist = ReadingList(import_path)

    for entry in rlist.entries:
        try:
            print(entry['title'])

            objs = RssSourceEntryDataModel.objects.filter(link = entry['url'])
            if objs.exists():
                print(entry['title'] + ", Skipping")
                summary_text += entry['title'] + " " + entry['url'] + ": Skipping, already in DB\n"
                continue
            else:
                p = Page(entry['url'])
                if not p.get_domain():
                    summary_text += entry['title'] + " " + entry['url'] + ": NOK - could not find domain\n"
                    continue

                lang = p.get_language()
                if not lang:
                    summary_text += entry['title'] + " " + entry['url'] + ": NOK - could not find language\n"
                    continue

                ent = RssSourceEntryDataModel(
                        source = p.get_domain(),
                        title = entry['title'],
                        description = entry['description'],
                        link = entry['url'],
                        date_published = entry['date'],
                        persistent = True,
                        dead = False,
                        user = "Thomas Pain",
                        language = lang)

                ent.save()

                summary_text += entry['title'] + " " + entry['url'] + ": OK \n"
        except Exception as e:
            summary_text += entry['title'] + " " + entry['url'] + ": NOK \n"

    context["summary_text"] = summary_text
    return render(request, app_name / 'summary_present.html', context)
