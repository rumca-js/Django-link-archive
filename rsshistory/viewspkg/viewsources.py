from django.views import generic
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlencode

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..controllers import (
    SourceDataController,
    SourceDataBuilder,
    LinkDataController,
    BackgroundJobController,
    LinkDataWrapper,
    SearchEngines,
)
from ..forms import SourceForm, SourcesChoiceForm
from ..queryfilters import SourceFilter
from ..views import ViewPage
from ..configuration import Configuration
from ..webtools import Url


class RssSourceListView(generic.ListView):
    model = SourceDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(RssSourceListView, self).get(*args, **kwargs)

    def get_queryset(self):
        self.query_filter = SourceFilter(self.request.GET)
        return self.query_filter.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssSourceListView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)
        # Create any data and add it to the context

        self.init_display_type(context)

        self.filter_form = SourcesChoiceForm(self.request.GET)
        self.filter_form.create()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse("{}:sources".format(LinkDatabase.name))

        context["query_filter"] = self.query_filter

        context["filter_form"] = self.filter_form
        context["page_title"] += " - news source list"

        return context

    def init_display_type(self, context):
        # TODO https://stackoverflow.com/questions/57487336/change-value-for-paginate-by-on-the-fly
        # if type is not normal, no pagination
        if "type" in self.request.GET:
            context["type"] = self.request.GET["type"]
        else:
            context["type"] = "normal"
        context["args"] = self.get_args()

    def get_args(self):
        arg_data = {}
        for arg in self.request.GET:
            if arg != "type":
                arg_data[arg] = self.request.GET[arg]

        return "&" + urlencode(arg_data)


class RssSourceDetailView(generic.DetailView):
    model = SourceDataController

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super(RssSourceDetailView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        context["page_title"] = self.object.title
        context["page_thumbnail"] = self.object.favicon
        context["search_engines"] = SearchEngines(self.object.title, self.object.url)
        try:
            context["handler"] = SourceControllerBuilder.get(self.object.url)
        except:
            pass

        return context


def add_source(request):
    p = ViewPage(request)
    p.set_title("Add source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        method = "POST"

        form = SourceForm(request.POST)

        if form.is_valid():
            b = SourceDataBuilder()
            b.link_data = form.cleaned_data
            b.manual_entry = True
            source = b.add_from_props()

            if not source:
                p.context["summary_text"] = "Source already exist"
                return p.render("summary_present.html")

            return HttpResponseRedirect(source.get_absolute_url())
        else:
            error_message = "\n".join(
                [
                    "{}: {}".format(field, ", ".join(errors))
                    for field, errors in form.errors.items()
                ]
            )

            p.context[
                "summary_text"
            ] = "Data: Could not add source {} <div>Data: {}</div>".format(
                error_message, form.cleaned_data
            )
            return p.render("summary_present.html")

    else:
        form = SourceForm()
        form.method = "POST"
        form.action_url = reverse("{}:source-add".format(LinkDatabase.name))

        p.context["form"] = form
        p.context["form_title"] = "Add new source"

        form_text = "<pre>"
        form_text += " - Specify all fields, if possible\n"
        form_text += " - if favicon is not specified, it is set to domain/favicon.ico\n"
        form_text += "</pre>"

        p.context["form_description_post"] = form_text

    return p.render("form_source_add.html")


def add_source_simple(request):
    from ..forms import SourceInputForm
    from ..controllers import SourceDataController

    def get_add_link_form(p, url):
        if not Url.is_web_link(url):
            p.context["summary_text"] = "Only http links are allowed. Link:{}".format(
                url
            )
            return p.render("summary_present.html")

        ob = SourceDataController.objects.filter(url=url)
        if ob.exists():
            p.context["form"] = form
            p.context["source"] = ob[0]

            return HttpResponseRedirect(ob[0].get_absolute_url())

        data = SourceDataController.get_full_information({"url": url})
        print(data)

        form = SourceForm(initial=data)
        form.method = "POST"
        form.action_url = reverse("{}:source-add".format(LinkDatabase.name))

        p.context["form"] = form

        return p.render("form_source_add.html")

    p = ViewPage(request)
    p.set_title("Add source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = SourceInputForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]

            return get_add_link_form(p, url)

        p.context["form"] = form
    elif request.method == "GET" and "link" in request.GET:
        return get_add_link_form(p, request.GET["link"])
    else:
        form = SourceInputForm()
        form.method = "POST"

        p.context["form"] = form

    return p.render("form_source_add.html")


def edit_source(request, pk):
    p = ViewPage(request)
    p.set_title("Edit source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    sources = SourceDataController.objects.filter(id=pk)
    if not sources.exists():
        p.context["summary_text"] = "Source does not exist"
        return p.render("summary_present.html")

    ob = sources[0]

    if request.method == "POST":
        form = SourceForm(request.POST, instance=ob)
        p.context["form"] = form

        if form.is_valid():
            ob.edit(form.cleaned_data)

            return HttpResponseRedirect(ob.get_absolute_url())

        error_message = "\n".join(
            [
                "{}: {}".format(field, ", ".join(errors))
                for field, errors in form.errors.items()
            ]
        )

        p.context[
            "summary_text"
        ] = "Could not edit source {} <div>Data: {}</div>".format(
            error_message, form.cleaned_data
        )
        return p.render("summary_present.html")
    else:
        if not ob.favicon:
            icon = Url.get_favicon(ob.url)
            if icon:
                form = SourceForm(instance=ob, initial={"favicon": icon})
            else:
                form = SourceForm(instance=ob)
        else:
            form = SourceForm(instance=ob)

        form.method = "POST"
        form.action_url = reverse("{}:source-edit".format(LinkDatabase.name), args=[pk])
        p.context["form"] = form
        return p.render("form_basic.html")


def refresh_source(request, pk):
    from ..models import SourceOperationalData

    p = ViewPage(request)
    p.set_title("Refresh source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    sources = SourceDataController.objects.filter(id=pk)
    if not sources.exists():
        p.context["summary_text"] = "Source does not exist"
        return p.render("summary_present.html")

    source = sources[0]

    dynamic_data = source.get_dynamic_data()
    if dynamic_data is not None:
        op = source.dynamic_data
        op.date_fetched = None
        op.save()

    BackgroundJobController.download_rss(source, True)

    return HttpResponseRedirect(source.get_absolute_url())


def sources_manual_refresh(request):
    from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

    p = ViewPage(request)
    p.set_title("Refresh sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = SourceDataController.objects.all()

    try:
        for ob in objs:
            plugin = SourceControllerBuilder.get(source)
            plugin.check_for_data()
    except Exception as E:
        print(str(E))

    return HttpResponseRedirect(reverse("{}:sources".format(LinkDatabase.name)))


def remove_source(request, pk):
    p = ViewPage(request)
    p.set_title("Remove source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ft = SourceDataController.objects.filter(id=pk)
    if ft.exists():
        source_url = ft[0].url
        ft.delete()

        return HttpResponseRedirect(reverse("{}:sources".format(LinkDatabase.name)))
    else:
        p.context["summary_text"] = "No source for ID: " + str(pk)

    return p.render("summary_present.html")


def source_remove_entries(request, pk):
    p = ViewPage(request)
    p.set_title("Remove source entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ft = SourceDataController.objects.filter(id=pk)
    if ft.exists():
        entries = LinkDataController.objects.filter(source=ft[0].url)
        if entries.exists():
            entries.delete()

            return HttpResponseRedirect(
                reverse(
                    "{}:source-detail".format(LinkDatabase.name),
                    kwargs={"pk": pk},
                )
            )
        else:
            p.context["summary_text"] = "No entries to remove"
    else:
        p.context["summary_text"] = "No source for ID: " + str(pk)

    return p.render("summary_present.html")


def remove_all_sources(request):
    p = ViewPage(request)
    p.set_title("Remove all sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ft = SourceDataController.objects.all()
    if ft.exists():
        ft.delete()

        return HttpResponseRedirect(reverse("{}:sources".format(LinkDatabase.name)))
    else:
        p.context["summary_text"] = "No source to remove"

    return p.render("summary_present.html")


def enable_all_sources(request):
    p = ViewPage(request)
    p.set_title("Remove all sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    sources = SourceDataController.objects.filter(on_hold=True)
    if sources.exists():
        for source in sources:
            source.enable()

        return HttpResponseRedirect(reverse("{}:sources".format(LinkDatabase.name)))
    else:
        p.context["summary_text"] = "No source to remove"


def wayback_save(request, pk):
    p = ViewPage(request)
    p.set_title("Wayback save")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if Configuration.get_object().config_entry.source_save:
        source = SourceDataController.objects.get(id=pk)
        BackgroundJobController.link_save(subject=source.url)

        return HttpResponseRedirect(
            reverse(
                "{}:source-detail".format(LinkDatabase.name),
                kwargs={"pk": pk},
            )
        )
    else:
        p.context["summary_text"] = "Waybacksave is disabled for sources"

    return p.render("summary_present.html")


def process_source_text(request, pk):
    p = ViewPage(request)
    p.set_title("Process source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    text = """
    """

    from ..pluginsources.rsssourceprocessor import RssSourceProcessor

    source = SourceDataController.objects.get(id=pk)

    proc = RssSourceProcessor()
    proc.process_parser_source(source, text)

    return HttpResponseRedirect(
        reverse(
            "{}:source-detail".format(LinkDatabase.name),
            kwargs={"pk": pk},
        )
    )


def import_youtube_links_for_source(request, pk):
    from ..programwrappers.ytdlp import YTDLP

    p = ViewPage(request)
    p.set_title("Import YouTube links for source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary_text = ""

    source_obj = SourceDataController.objects.get(id=pk)

    url = str(source_obj.url)
    wh = url.find("=")

    if wh == -1:
        p.context["summary_text"] = "Could not obtain code from a video"
        return p.render("summary_present.html")

    code = url[wh + 1 :]
    channel = "https://www.youtube.com/channel/{}".format(code)
    ytdlp = YTDLP(channel)
    print(
        "Searching for links for source {} channel {}".format(source_obj.title, channel)
    )
    links = ytdlp.get_channel_video_list()

    data = {"user": None, "language": source_obj.language, "bookmarked": False}

    print("Found source links: {}".format(len(links)))

    for link in links:
        print("Adding job {}".format(link))
        wrapper = LinkDataWrapper(link=link)
        if not wrapper.get():
            BackgroundJobController.link_add(link, source_obj)

    p.context["summary_text"] = ""
    return p.render("summary_present.html")


def source_fix_entries(request, source_pk):
    p = ViewPage(request)
    p.set_title("Fix source entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    source_obj = SourceDataController.objects.get(id=source_pk)

    entries = LinkDataController.objects.filter(source=source_obj.url)

    summary_text = "Fixed following items:"

    for entry in entries:
        if entry.language != source_obj.language:
            entry.language = source_obj.language
            entry.save()
            summary_text += "Fixed {} {}\n".format(entry.title, entry.link)
        if not entry.source_obj:
            entry.source_obj = source_obj
            entry.save()
            summary_text += "Fixed {} {}\n".format(entry.title, entry.link)

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def source_json(request, pk):
    sources = SourceDataController.objects.filter(id=pk)

    if sources.count() == 0:
        p = ViewPage(request)
        p.set_title("Source JSON")
        p.context["summary_text"] = "No such source in the database {}".format(pk)
        return p.render("summary_present.html")

    source = sources[0]

    from ..serializers.instanceimporter import InstanceExporter

    exporter = InstanceExporter()
    json_obj = exporter.export_source(source)

    # JsonResponse
    return JsonResponse(json_obj)


def sources_json(request):
    # Data
    query_filter = SourceFilter(request.GET)
    query_filter.use_page_limit = True
    sources = query_filter.get_filtered_objects()

    from ..serializers.instanceimporter import InstanceExporter

    exporter = InstanceExporter()
    json_obj = exporter.export_sources(sources)

    # JsonResponse
    return JsonResponse(json_obj)
