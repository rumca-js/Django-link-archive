
from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..models import SourceDataModel, LinkDataModel, LinkTagsDataModel, ConfigurationEntry
from ..prjconfig import Configuration
from ..forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, EntryChoiceForm, ConfigForm, CommentEntryForm


def init_context(request, context):
    from ..views import init_context
    return init_context(request, context)

def get_context(request):
    from ..views import get_context
    return get_context(request)

def get_app():
    from ..views import app_name
    return app_name


class RssEntriesListView(generic.ListView):
    model = LinkDataModel
    context_object_name = 'entries_list'
    paginate_by = 200

    def get_queryset(self):
        self.filter_form = EntryChoiceForm(args = self.request.GET)
        return self.filter_form.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssEntriesListView, self).get_context_data(**kwargs)
        context = init_context(self.request, context)
        # Create any data and add it to the context

        self.filter_form.create()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse('rsshistory:entries')

        app_name = get_app()
        c = Configuration.get_object(str(app_name))
        threads = c.get_threads()
        if threads:
           thread = c.get_threads()[0]
           queue_size = thread.get_queue_size()
           context['rss_are_fetched'] = queue_size > 0
           context['rss_queue_size'] = queue_size

        context['filter_form'] = self.filter_form
        context['page_title'] += " - entries"

        from django_user_agents.utils import get_user_agent
        user_agent = get_user_agent(self.request)
        context["is_mobile"] = user_agent.is_mobile

        return context


class RssEntryDetailView(generic.DetailView):
    model = LinkDataModel

    def get_context_data(self, **kwargs):
        from ..handlers.linkcontrollerbuilder import LinkControllerBuilder

        # Call the base implementation first to get the context
        context = super(RssEntryDetailView, self).get_context_data(**kwargs)
        context = init_context(self.request, context)

        if self.object.language == None:
            self.object.update_language()

        context['page_title'] += " - " + self.object.title
        context['object_controller'] = LinkControllerBuilder.get_controller(self.object)

        from ..sources.waybackmachine import WaybackMachine
        from ..dateutils import DateUtils
        m = WaybackMachine()
        context['archive_org_date'] = m.get_formatted_date(DateUtils.get_date_today())

        return context


def add_entry(request):
    context = get_context(request)
    context['page_title'] += " - Add entry"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = EntryForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            data = form.get_full_information()

            ob = LinkDataModel.objects.filter(link=data['link'])
            if ob.exists():
                context['form'] = form
                context['entry'] = ob[0]

                return render(request, get_app() / 'entry_edit_exists.html', context)

            if not form.save_form(data):
                context["summary_text"] = "Could not save link"
                return render(request, get_app() / 'summary_present.html', context)

            context['form'] = form

            link = data['link']

            ob = LinkDataModel.objects.filter(link = link)
            if ob.exists():
                context['entry'] = ob[0]

            c = Configuration.get_object(str(get_app()))
            if not c.thread_mgr:
                context['summary_text'] = "Source added, but could not add to queue - missing threads"
                return render(request, get_app() / 'entry_added.html', context)
            c.thread_mgr.wayback_save(link)

            return render(request, get_app() / 'entry_added.html', context)

        context["summary_text"] = "Form is invalid"
        return render(request, get_app() / 'summary_present.html', context)

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

        context['form_title'] = "Add new entry"

        form_text = "<pre>"
        form_text += "Required fields:\n"
        form_text += " - Link [required]\n"
        form_text += "\n"
        form_text += "For YouTube links:\n"
        form_text += " - Title, description, Date published, source, language is set automatically\n"
        form_text += " - manual setting of language overrides the default (en-US)\n"
        form_text += "\n"
        form_text += "For standard links:\n"
        form_text += " - Title, description, source, language is set automatically, if not specified\n"
        form_text += " - Always specify date published [required]\n"
        form_text += " - Better specify language\n"
        form_text += " - In case of errors, specify title, and description\n"
        form_text += "</pre>"

        context['form_description_post'] = form_text

    return render(request, get_app() / 'form_basic.html', context)


def edit_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit entry"

    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    obs = LinkDataModel.objects.filter(id=pk)
    if not obs.exists():
        context['summary_text'] = "Such entry does not exist"
        return render(request, get_app() / 'summary_present.html', context)

    ob = obs[0]
    if ob.user is None or ob.user == "":
        ob.user = str(request.user.username)
        ob.save()

    if request.method == 'POST':
        form = EntryForm(request.POST, instance=ob)
        context['form'] = form

        if form.is_valid():
            form.save()

            context['entry'] = ob
            return render(request, get_app() / 'entry_edit_ok.html', context)

        context['summary_text'] = "Could not edit entry"

        return render(request, get_app() / 'summary_present.html', context)
    else:
        form = EntryForm(instance=ob)
        #form.fields['user'].initial = request.user.username
        form.method = "POST"
        form.action_url = reverse('rsshistory:entry-edit', args=[pk])
        context['form'] = form
        return render(request, get_app() / 'form_basic.html', context)


def remove_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove entry"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    entry = LinkDataModel.objects.filter(id=pk)
    if entry.exists():
        entry.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return render(request, get_app() / 'summary_present.html', context)


def hide_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - hide entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    objs = LinkDataModel.objects.filter(id=pk)
    obj = objs[0]

    fav = obj.dead
    obj.dead = not obj.dead
    obj.save()

    summary_text = "Link changed to state: " + str(obj.dead)

    context["summary_text"] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def search_init_view(request):
    from ..forms import GoogleChoiceForm

    context = get_context(request)
    context['page_title'] += " - search view"

    filter_form = EntryChoiceForm(args = request.GET)
    filter_form.create()
    filter_form.method = "GET"
    filter_form.action_url = reverse('rsshistory:entries')

    context['form'] = filter_form

    return render(request, get_app() / 'form_search.html', context)

def make_persistent_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - persistent entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    entry = LinkDataModel.objects.get(id=pk)

    prev_state = entry.persistent

    entry.persistent = True
    entry.user = request.user.username
    entry.save()

    if prev_state != True:
       c = Configuration.get_object(str(get_app()))
       if not c.thread_mgr:
           context['summary_text'] = "Source added, but could not add to queue - missing threads"
           return render(request, get_app() / 'summary_present.html', context)
       c.thread_mgr.wayback_save(entry.link)

    summary_text = "Link changed to state: " + str(entry.persistent)

    context["summary_text"] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def make_not_persistent_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - persistent entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = LinkDataModel.objects.get(id=pk)

    tags = LinkTagsDataModel.objects.filter(link = ft.link)
    tags.delete()

    fav = ft.persistent
    ft.persistent = False
    ft.user = request.user.username
    ft.save()

    summary_text = "Link changed to state: " + str(ft.persistent)

    context["summary_text"] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def import_entries(request):
    # TODO
    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import entries"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportEntriesForm(request.POST)

        if form.is_valid():
            summary_text = "Import entries log\n"

            for entry in form.get_entries():

                if LinkDataModel.objects.filter(url=entry.url).exists():
                    summary_text += entry.title + " " + entry.url + " " + " Error: Already present in db\n"
                else:
                    try:
                        record = LinkDataModel(url=entry.url,
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
        return render(request, get_app() / 'entries_import_summary.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ImportEntriesForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:entries-import')
        context["form"] = form
        return render(request, get_app() / 'form_basic.html', context)


class NotBookmarkedView(generic.ListView):
    model = LinkDataModel
    context_object_name = 'entries_list'
    paginate_by = 200
    template_name = get_app() / 'entries_untagged_view.html'

    def get_queryset(self):
        return LinkDataModel.objects.filter(tags__tag__isnull = True, persistent = True)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(NotBookmarkedView, self).get_context_data(**kwargs)
        context = init_context(self.request, context)
        # Create any data and add it to the context

        return context
