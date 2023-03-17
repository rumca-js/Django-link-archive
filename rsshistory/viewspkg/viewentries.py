
from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..models import RssSourceDataModel, RssSourceEntryDataModel, RssEntryTagsDataModel, ConfigurationEntry
from ..prjconfig import Configuration
from ..forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, EntryChoiceForm, ConfigForm, CommentEntryForm


def init_context(context):
    from ..views import init_context
    return init_context(context)

def get_context(request):
    from ..views import get_context
    return get_context(request)

def get_app():
    from ..views import app_name
    return app_name


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
    model = RssSourceEntryDataModel

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssEntryDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        if self.object.language == None:
            self.object.update_language()

        context['page_title'] += " - " + self.object.title

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

        ob = RssSourceEntryDataModel.objects.filter(link=request.POST.get('link'))
        if ob.exists():
            context['form'] = form
            context['entry'] = ob[0]

            return render(request, get_app() / 'entry_edit_exists.html', context)

        # check whether it's valid:
        if form.is_valid():
            if not form.save_form():
                context["summary_text"] = "Could not add link"
                return render(request, get_app() / 'summary_present.html', context)

            context['form'] = form

            link = request.POST.get('link')

            ob = RssSourceEntryDataModel.objects.filter(link = link)
            if ob.exists():
                context['entry'] = ob[0]

            c = Configuration.get_object(str(get_app()))
            c.thread_mgr.wayback_save(link)

            return render(request, get_app() / 'entry_added.html', context)

        context["summary_text"] = "Could not add link"
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

    return render(request, get_app() / 'form_basic.html', context)


def edit_entry(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit entry"

    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    obs = RssSourceEntryDataModel.objects.filter(id=pk)
    if not obs.exists():
        context['summary_text'] = "Such entry does not exist"
        return render(request, get_app() / 'summary_present.html', context)

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

    entry = RssSourceEntryDataModel.objects.filter(id=pk)
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

    objs = RssSourceEntryDataModel.objects.filter(id=pk)
    obj = objs[0]

    fav = obj.dead
    obj.dead = not obj.dead
    obj.save()

    summary_text = "Link changed to state: " + str(obj.dead)

    context["summary_text"] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def tag_entry(request, pk):
    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/
    from ..forms import TagEntryForm
    from ..models import RssEntryTagsDataModel

    context = get_context(request)
    context['page_title'] += " - tag entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    objs = RssSourceEntryDataModel.objects.filter(id=pk)

    if not objs.exists():
        context["summary_text"] = "Sorry, such object does not exist"
        return render(request, get_app() / 'summary_present.html', context)

    obj = objs[0]
    if not obj.persistent:
        context["summary_text"] = "Sorry, only persistent objects can be tagged"
        return render(request, get_app() / 'summary_present.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = TagEntryForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            form.save_tags()

            context["summary_text"] = "Entry tagged"
            return render(request, get_app() / 'summary_present.html', context)
        else:
            context["summary_text"] = "Entry not added"
            return render(request, get_app() / 'summary_present.html', context)

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

    return render(request, get_app() / 'form_basic.html', context)


def search_init_view(request):
    from ..models import RssEntryTagsDataModel
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

    entry = RssSourceEntryDataModel.objects.get(id=pk)

    prev_state = entry.persistent

    entry.persistent = True
    entry.user = request.user.username
    entry.save()

    if prev_state != True:
       c = Configuration.get_object(str(get_app()))
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

    ft = RssSourceEntryDataModel.objects.get(id=pk)

    tags = RssEntryTagsDataModel.objects.filter(link = ft.link)
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
        return render(request, get_app() / 'entries_import_summary.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ImportEntriesForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:entries-import')
        context["form"] = form
        return render(request, get_app() / 'form_basic.html', context)


class NotBookmarkedView(generic.ListView):
    model = RssSourceEntryDataModel
    context_object_name = 'entries_list'
    paginate_by = 200
    template_name = get_app() / 'entries_untagged_view.html'

    def get_queryset(self):
        return RssSourceEntryDataModel.objects.filter(tags__tag__isnull = True, persistent = True)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(NotBookmarkedView, self).get_context_data(**kwargs)
        context = init_context(context)
        # Create any data and add it to the context

        return context

