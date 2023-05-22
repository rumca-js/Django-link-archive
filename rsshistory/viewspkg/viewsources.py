
from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..models import SourceDataModel, LinkDataModel, ConfigurationEntry
from ..prjconfig import Configuration
from ..forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, ConfigForm, CommentEntryForm


def init_context(context):
    from ..views import init_context
    return init_context(context)

def get_context(request):
    from ..views import get_context
    return get_context(request)

def get_app():
    from ..views import app_name
    return app_name


class RssSourceListView(generic.ListView):
    model = SourceDataModel
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

        from django_user_agents.utils import get_user_agent
        user_agent = get_user_agent(self.request)
        context["is_mobile"] = user_agent.is_mobile

        return context


class RssSourceDetailView(generic.DetailView):
    model = SourceDataModel

    def get_context_data(self, **kwargs):
        from ..handlers.sourcecontroller import SourceController
        # Call the base implementation first to get the context
        context = super(RssSourceDetailView, self).get_context_data(**kwargs)
        context = init_context(context)

        context['page_title'] += " - " + self.object.title
        context['handler'] = SourceController(self.object)

        return context


def add_source(request):
    context = get_context(request)
    context['page_title'] += " - add source"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = SourceForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            form.save()

            context["summary_text"] = "Source added"
            return render(request, get_app() / 'summary_present.html', context)
        else:
            context["summary_text"] = "Source not added"
            return render(request, get_app() / 'summary_present.html', context)

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

    return render(request, get_app() / 'form_basic.html', context)


def edit_source(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit source"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, get_app() / 'source_edit_does_not_exist.html', context)

    ob = ft[0]

    if request.method == 'POST':
        form = SourceForm(request.POST, instance=ob)
        context['form'] = form

        if form.is_valid():
            form.save()

            context['source'] = ob
            return render(request, get_app() / 'source_edit_ok.html', context)

        context['summary_text'] = "Could not edit source"

        return render(request, get_app() / 'summary_present.html', context)
    else:
        if not ob.favicon:
            from ..webtools import Page
            p = Page(ob.url)

            form = SourceForm(instance=ob, initial={'favicon' : p.get_domain() +"/favicon.ico" })
        else:
            form = SourceForm(instance=ob)

        form.method = "POST"
        form.action_url = reverse('rsshistory:source-edit', args=[pk])
        context['form'] = form
        return render(request, get_app() / 'form_basic.html', context)


def refresh_source(request, pk):
    from ..models import SourceOperationalData

    context = get_context(request)
    context['page_title'] += " - refresh source"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, get_app() / 'source_edit_does_not_exist.html', context)

    ob = ft[0]

    operational = SourceOperationalData.objects.filter(url = ob.url)
    if operational.exists():
        op = operational[0]
        op.date_fetched = None
        op.save()

    c = Configuration.get_object(str(get_app()))
    if not c.thread_mgr:
        context['summary_text'] = "Source added, but could not add to queue - missing threads"
        return render(request, get_app() / 'summary_present.html', context)

    c.thread_mgr.download_rss(ob, True)

    context['summary_text'] = "Source added to refresh queue"
    return render(request, get_app() / 'summary_present.html', context)


def import_sources(request):
    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import sources"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportSourcesForm(request.POST)

        if form.is_valid():
            for source in form.get_sources():

                if SourceDataModel.objects.filter(url=source.url).exists():
                    summary_text += source.title + " " + source.url + " " + " Error: Already present in db\n"
                else:
                    record = SourceDataModel(url=source.url,
                                                title=source.title,
                                                category=source.category,
                                                subcategory=source.subcategory)
                    record.save()
                    summary_text += source.title + " " + source.url + " " + " OK\n"
        else:
            summary_text = "Form is invalid"

        context["form"] = form
        context['summary_text'] = summary_text
        return render(request, get_app() / 'sources_import_summary.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ImportSourcesForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:sources-import')
        context["form"] = form
        return render(request, get_app() / 'form_basic.html', context)


def remove_source(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove source"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.filter(id=pk)
    if ft.exists():
        source_url = ft[0].url
        ft.delete()
        
        # TODO checkbox - or other button to remove corresponding entries
        #entries = LinkDataModel.objects.filter(url = source_url)
        #if entries.exists():
        #    entries.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return render(request, get_app() / 'summary_present.html', context)


def remove_all_sources(request):
    context = get_context(request)
    context['page_title'] += " - remove all links"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.all()
    if ft.exists():
        ft.delete()
        context["summary_text"] = "Removing all sources ok"
    else:
        context["summary_text"] = "No source to remove"

    return render(request, get_app() / 'summary_present.html', context)


def export_sources(request):
    context = get_context(request)
    context['page_title'] += " - export data"
    summary_text = ""

    c = Configuration.get_object(str(get_app()))

    from ..datawriter import DataWriter
    writer = DataWriter(c)
    writer.write_sources()

    context["summary_text"] = converter.export()

    return render(request, get_app() / 'summary_present.html', context)


def wayback_save(request, pk):
    context = get_context(request)
    context['page_title'] += " - Waybacksave"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    source = SourceDataModel.objects.get(id=pk)
    c = Configuration.get_object(str(get_app()))
    c.wayback_save(source.url)

    context["summary_text"] = "Added to waybacksave"

    return render(request, get_app() / 'summary_present.html', context)


def import_youtube_links_for_source(request, pk):
    from ..programwrappers.ytdlp import YTDLP

    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import sources"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    source_obj = SourceDataModel.objects.get(id = pk)
    url = str(source_obj.url)
    wh = url.find("=")

    if wh == -1:
        context['summary_text'] = "Could not obtain code from a video"
        return render(request, get_app() / 'summary_present.html', context)

    code = url[wh + 1 :]
    channel = 'https://www.youtube.com/channel/{}'.format(code)
    ytdlp = YTDLP(channel)
    links = ytdlp.get_channel_video_list()

    data = {"user" : None, "language" : source_obj.language, "persistent" : False}

    for link in links:
       print("Adding {}".format(link))
       try:
           LinkDataModel.create_from_youtube(link, data)
       except Exception as E:
           try:
               LinkDataModel.create_from_youtube(link, data)
           except Exception as E:
               pass

       summary_text += "\n{}".format(link)

    context['summary_text'] = summary_text
    return render(request, get_app() / 'summary_present.html', context)
