from pathlib import Path
from datetime import datetime, date, timedelta
import traceback

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from django.db.models.query import QuerySet
from django.db.models.query import EmptyQuerySet

from .models import RssSourceDataModel, RssSourceEntryDataModel, RssEntryTagsDataModel, ConfigurationEntry
from .models import RssSourceImportHistory, RssSourceExportHistory
from .serializers.converters import ModelCollectionConverter, CsvConverter

from .forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, EntryChoiceForm, ConfigForm, CommentEntryForm
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

        context['page_title'] += " - " + self.object.title

        return context


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

        from .sources.waybackmachine import WaybackMachine
        from .dateutils import DateUtils
        m = WaybackMachine()
        context['archive_org_date'] = m.get_formatted_date(DateUtils.get_date_today())

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
        form.action_url = reverse('rsshistory:source-add')
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
        form.action_url = reverse('rsshistory:source-edit', args=[pk])
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
    c.thread_mgr.download_rss(ob, True)

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
        form.action_url = reverse('rsshistory:sources-import')
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
        form.action_url = reverse('rsshistory:entries-import')
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

    c = Configuration.get_object(str(app_name))

    from .datawriter import DataWriter
    writer = DataWriter(c)
    writer.write_sources()

    context["summary_text"] = converter.export()

    return render(request, app_name / 'summary_present.html', context)


def configuration(request):
    context = get_context(request)
    context['page_title'] += " - Configuration"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)
    
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


def system_status(request):
    context = get_context(request)
    context['page_title'] += " - Status"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)
    
    c = Configuration.get_object(str(app_name))
    #c.write_bookmarks()
    size_b = get_directory_size_bytes(c.directory)
    size_kb = size_b / 1024
    size_mb = size_kb / 1024

    context['directory'] = c.directory
    context['database_size_bytes'] = size_b
    context['database_size_kbytes'] = size_kb
    context['database_size_mbytes'] = size_mb

    from .models import PersistentInfo
    context['log_items'] = PersistentInfo.objects.all()

    threads = c.get_threads()
    for thread in threads:
        items = thread.get_processs_list()

    context['thread_list'] = threads
    context['server_path'] = Path(".").resolve()
    context['directory'] = Path(".").resolve()

    history = RssSourceImportHistory.objects.all().order_by('date')[:100]
    context['import_history_list'] = history

    history = RssSourceExportHistory.objects.all()
    context['export_history_list'] = history

    return render(request, app_name / 'system_status.html', context)


def write_bookmarks(request):
    context = get_context(request)
    context['page_title'] += " - Writer bookmarks"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    from .datawriter import DataWriter
    
    c = Configuration.get_object(str(app_name))
    writer = DataWriter(c)
    writer.write_bookmarks()

    context["summary_text"] = "Wrote OK"

    return render(request, app_name / 'summary_present.html', context)


def make_persistent_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - persistent entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    entry = RssSourceEntryDataModel.objects.get(id=pk)

    prev_state = entry.persistent

    entry.persistent = True
    entry.user = request.user.username
    entry.save()

    if prev_state != True:
       c = Configuration.get_object(str(app_name))
       c.thread_mgr.wayback_save(entry.link)

    summary_text = "Link changed to state: " + str(entry.persistent)

    context["summary_text"] = summary_text

    return render(request, app_name / 'summary_present.html', context)


def make_not_persistent_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - persistent entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    ft = RssSourceEntryDataModel.objects.get(id=pk)

    tags = RssEntryTagsDataModel.objects.filter(link = ft.link)
    tags.delete()

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
            if not form.save_form():
                context["summary_text"] = "Could not add link"
                return render(request, app_name / 'summary_present.html', context)

            context['form'] = form

            link = request.POST.get('link')

            ob = RssSourceEntryDataModel.objects.filter(link = link)
            if ob.exists():
                context['entry'] = ob[0]

            c = Configuration.get_object(str(app_name))
            c.thread_mgr.wayback_save(link)

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
        form.action_url = reverse('rsshistory:entry-add')
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
        form.action_url = reverse('rsshistory:entry-edit', args=[pk])
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
        form.action_url = reverse('rsshistory:entry-tag', args=[pk])
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
    from .serializers.readinglist import ReadingList
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


def truncate_errors(request):
    context = get_context(request)
    context['page_title'] += " - clearing errors"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    from .models import PersistentInfo
    PersistentInfo.truncate()

    context["summary_text"] = "Clearing errors done"

    return render(request, app_name / 'summary_present.html', context)


def data_errors_page(request):
    def fix_source_entry_links():
        print("fix_source_entry_links")

        entries_no_object = RssSourceEntryDataModel.objects.filter(source_obj = None)
        for entry in entries_no_object:
            source = RssSourceDataModel.objects.filter(url = entry.source)
            if source.exists():
                entry.source_obj = source[0]
                entry.save()
                #summary_text += "Fixed {0}, added source object\n".format(entry.link)
                print("Fixed {0}, added source object".format(entry.link))
        print("fix_source_entry_links done")

    def fix_tags_links():
        print("fix_tags_links")

        tags = RssEntryTagsDataModel.objects.all()
        for tag in tags:
            removed = False

            links = RssSourceEntryDataModel.objects.filter(link = tag.link)
            for link in links:
                if not link.persistent:
                    print("Removed tag")
                    tag.delete()
                    removed = True
                    continue

            if removed:
                continue
        print("fix_tags_links done")

    def push_main_repo():
        ob = ConfigurationEntry.objects.all()
        if ob.exists():
            conf = ob[0]
            c = Configuration.get_object(str(app_name))
            print("Git pushing")
            c.push_bookmarks_repo(conf)
            print("Git ready")

    def incorrect_language():
        from django.db.models import Q
        criterion1 = Q(language__contains="pl")
        criterion2 = Q(language__contains="en")
        criterion3 = Q(language__isnull = True)

        entries_no_object = RssSourceEntryDataModel.objects.filter(~criterion1 & ~criterion2 & ~criterion3, persistent = True)

        if entries_no_object.exists():
            return entries_no_object

    def incorrect_youtube():
        from django.db.models import Q
        criterion1 = Q(link__contains="m.youtube")

        # only fix those that have youtube in source. leave other RSS sources
        criterion2 = Q(link__contains="https://www.youtube.com")
        criterion3 = Q(source__contains="youtube")
        criterion4 = Q(source__contains="https://www.youtube.com/feeds")

        criterion5 = Q(source__isnull = True)

        entries_no_object = RssSourceEntryDataModel.objects.filter(criterion1)
        entries_no_object |= RssSourceEntryDataModel.objects.filter(criterion2 & criterion3 & ~criterion4)
        entries_no_object |= RssSourceEntryDataModel.objects.filter(criterion2 & criterion5)

        if entries_no_object.exists():
            return entries_no_object

    def fix_incorrect_youtube(entries):
        from .linkhandlers.youtubelinkhandler import YouTubeLinkHandler

        for entry in entries:
            print("Fixing: {} {} {}".format(entry.link, entry.title, entry.source))
            h = YouTubeLinkHandler(entry.link)
            h.download_details()

            chan_url = h.get_channel_feed_url()
            link_valid = h.get_link_url()
            if chan_url:
                entry.source = chan_url
                entry.link = link_valid
                entry.save()
                print("Fixed: {} {} {}".format(entry.link, entry.title, chan_url))
            else:
                print("Not fixed: {}".format(entry.link, entry.title))


    context = get_context(request)
    context['page_title'] += " - data errors"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    #fix_source_entry_links()
    #fix_tags_links()
    # push_main_repo()

    incorrect_youtube_entries = incorrect_youtube()
    #fix_incorrect_youtube(incorrect_youtube_entries)

    summary_text = "Done"
    try:
        context['links_incorrect_language'] = incorrect_language()
        context['links_incorrect_youtube'] = incorrect_youtube_entries
    except Exception as e:
        traceback.print_exc(file=sys.stdout)

    # find links without source

    # remove tags, for which we do not have links, or entry is not bookmarked

    # show bookmarked links without tags

    return render(request, app_name / 'data_errors.html', context)


def show_tags(request):

    context = get_context(request)
    context['page_title'] += " - browse tags"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    # TODO select only this month
    objects = RssEntryTagsDataModel.objects.all()

    tags = objects.values('tag')

    result = {}
    for item in tags:
        tag = item['tag']
        if tag in result:
            result[item['tag']] += 1
        else:
            result[item['tag']] = 1

    result_list = []
    for item in result:
        result_list.append([item, result[item]])

    def map_func(elem):
        return elem[1]

    result_list = sorted(result_list, key = map_func, reverse=True)

    text = ""
    for tag in result_list:
        link = reverse('rsshistory:entries') + "?tag="+tag[0]
        link_text = str(tag[0]) + " " + str(tag[1])
        text += "<div><a href=\"{0}\" class=\"simplebutton\">{1}</a></div>".format(link, link_text)

    context["summary_text"] = text

    return render(request, app_name / 'tags_view.html', context)


def import_source_from_ia_impl(wb, source_url, source_archive_url, archive_time):
    print("Reading from time: {0} {1}".format(source_url, archive_time))

    source_obj = RssSourceDataModel.objects.filter(url = source_url)[0]

    if len(RssSourceImportHistory.objects.filter(url = source_obj.url, date = archive_time)) != 0:
        print("Import timestamp exists")
        return False

    c = Configuration.get_object(str(app_name))

    from .sources.rsssourceprocessor import RssSourceProcessor

    proc = RssSourceProcessor(c)
    proc.allow_adding_with_current_time = False
    proc.default_entry_timestamp = archive_time
    entries = proc.process_rss_source(source_obj, source_archive_url)

    if entries == 0:
        print("No entry read")
        return False

    print("Internet archive done {0}".format(source_url))

    if len(RssSourceImportHistory.objects.filter(url = source_obj.url, date = archive_time)) == 0:
        history = RssSourceImportHistory(url = source_obj.url, date = archive_time, source_obj = source_obj)
        history.save()

    return True


def get_time_stamps(url, start_time, stop_time):

   time = stop_time
   while time >= start_time:
       if len(RssSourceImportHistory.objects.filter(url = url, date = time)) != 0:
           time -= timedelta(days = 1)
           print("Skipping already imported timestamp {0} {1}".format(url, time))
           continue

       yield time
       time -= timedelta(days = 1)


def import_source_from_ia_range_impl(source_url, archive_start, archive_stop):
    from .sources.waybackmachine import WaybackMachine
    wb = WaybackMachine()

    for timestamp in get_time_stamps(source_url, archive_start, archive_stop):
        archive_url = wb.get_archive_url(source_url, timestamp)
        if not archive_url:
            print("Could not find archive link for timestamp {0} {1}".format(source_url, timestamp))
            continue

        print("Processing {0} {1} {2}".format(timestamp, source_url, archive_url))

        if import_source_from_ia_impl(wb, source_url, archive_url, timestamp) == False:
            print("Could not import feed for time: {0} {1} {2}".format(source_url, archive_url, timestamp))


def import_source_from_ia(request, pk):
    from .forms import ImportSourceRangeFromInternetArchiveForm

    context = get_context(request)
    context['page_title'] += " - Import internet archive"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    if request.method == 'POST':
        form = ImportSourceRangeFromInternetArchiveForm(request.POST)
        if form.is_valid():
            source_url = form.cleaned_data['source_url']
            archive_start = form.cleaned_data['archive_start']
            archive_stop = form.cleaned_data['archive_stop']

            if import_source_from_ia_range_impl(source_url, archive_start, archive_stop) == False:
                context["summary_text"] = "Could not read internet archive"
                return render(request, app_name / 'summary_present.html', context)
            else:
                context["summary_text"] = "Internet archive data read successfully"
                return render(request, app_name / 'summary_present.html', context)
    
    source_obj = RssSourceDataModel.objects.get(id = pk)
    
    form = ImportSourceRangeFromInternetArchiveForm(initial={"source_url": source_obj.url, 
             'archive_start' : date.today() - timedelta(days = 1),
             'archive_stop' : date.today()})
    form.method = "POST"
    #form.action_url = reverse('rsshistory:configuration')

    context['form'] = form

    return render(request, app_name / 'import_internetarchive.html', context)


def untagged_bookmarks(request):
    context = get_context(request)
    context['page_title'] += " - Find not tagged entries"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    links = RssSourceEntryDataModel.objects.filter(tags__tag__isnull = True)
    context['links'] = links

    return render(request, app_name / 'entries_untagged.html', context)


class NotBookmarkedView(generic.ListView):
    model = RssSourceEntryDataModel
    context_object_name = 'entries_list'
    paginate_by = 200
    template_name = app_name / 'entries_untagged_view.html'

    def get_queryset(self):
        return RssSourceEntryDataModel.objects.filter(tags__tag__isnull = True, persistent = True)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(NotBookmarkedView, self).get_context_data(**kwargs)
        context = init_context(context)
        # Create any data and add it to the context

        return context


def wayback_save(request, pk):
    context = get_context(request)
    context['page_title'] += " - Waybacksave"

    if not request.user.is_staff:
        return render(request, app_name / 'missing_rights.html', context)

    source = RssSourceDataModel.objects.get(id=pk)
    c = Configuration.get_object(str(app_name))
    c.wayback_save(source.url)

    context["summary_text"] = "Added to waybacksave"

    return render(request, app_name / 'summary_present.html', context)


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


def show_youtube_link_props(request):
    context = get_context(request)
    context['page_title'] += " - show youtube link properties"

    from .forms import YouTubeLinkSimpleForm

    youtube_link = "https:"
    if not request.method == 'POST':
        form = YouTubeLinkSimpleForm(initial={'youtube_link' : youtube_link})
        form.method = "POST"
        form.action_url = reverse('rsshistory:show-youtube-link-props')
        context['form'] = form

        return render(request, app_name / 'form_basic.html', context)

    else:
        form = YouTubeLinkSimpleForm(request.POST)
        if not form.is_valid():

            context["summary_text"] = "Form is invalid"

            return render(request, app_name / 'summary_present.html', context)
        else:
            from .linkhandlers.youtubelinkhandler import YouTubeLinkHandler

            youtube_link = form.cleaned_data['youtube_link']

            handler = YouTubeLinkHandler(youtube_link)
            handler.download_details()

            yt_json = handler.yt_ob.get_json()
            rd_json = handler.rd_ob.get_json()

            yt_props = str(yt_json)
            rd_props = str(rd_json)

            feed_url = handler.yt_ob.get_channel_feed_url()

            yt_props = [('webpage_url', yt_json['webpage_url'])]
            yt_props.append( ('title', yt_json['title']) )
            yt_props.append( ('uploader_url', yt_json['uploader_url']) )
            yt_props.append( ('channel_url', yt_json['channel_url']) )
            yt_props.append( ('channel_feed_url', feed_url) )
            yt_props.append( ('channel_id', yt_json['channel_id']) )

            for yt_prop in yt_json:
                yt_props.append( (yt_prop, str(yt_json[yt_prop])) )

            rd_props = []
            for rd_prop in rd_json:
                rd_props.append( (rd_prop, str(rd_json[rd_prop])) )

            context["youtube_props"] = yt_props
            context["return_dislike_props"] = rd_props

            context["yt_props"] = yt_props
            context["rd_props"] = rd_props

            return render(request, app_name / 'show_youtube_link_props.html', context)
