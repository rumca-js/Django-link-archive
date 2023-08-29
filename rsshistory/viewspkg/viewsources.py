from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.http import JsonResponse

from ..models import BackgroundJob
from ..configuration import Configuration
from ..forms import SourceForm, SourcesChoiceForm, ConfigForm
from ..queryfilters import SourceFilter
from ..views import ContextData

from ..controllers import (
    SourceDataController,
    LinkDataController,
    BackgroundJobController,
)


class RssSourceListView(generic.ListView):
    model = SourceDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_queryset(self):
        self.query_filter = SourceFilter(self.request.GET)
        return self.query_filter.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssSourceListView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)
        # Create any data and add it to the context

        self.filter_form = SourcesChoiceForm(args=self.request.GET)
        self.filter_form.create(self.query_filter.filtered_objects)
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse("{}:sources".format(ContextData.app_name))

        context["query_filter"] = self.query_filter

        context["filter_form"] = self.filter_form
        context["page_title"] += " - news source list"

        return context


class RssSourceDetailView(generic.DetailView):
    model = SourceDataController

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super(RssSourceDetailView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        context["page_title"] = self.object.title
        try:
            context["handler"] = SourceControllerBuilder.get(self.object)
        except:
            pass

        return context


def add_source(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - add source"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        method = "POST"

        form = SourceForm(request.POST)

        if form.is_valid():
            SourceDataController.add(form.cleaned_data)

            context["summary_text"] = "Source added"
            return ContextData.render(request, "summary_present.html", context)
        else:
            context["summary_text"] = "Source not added"
            return ContextData.render(request, "summary_present.html", context)

    else:
        form = SourceForm()
        form.method = "POST"
        form.action_url = reverse("{}:source-add".format(ContextData.app_name))
        context["form"] = form

        context["form_title"] = "Add new source"

        form_text = "<pre>"
        form_text += " - Specify all fields, if possible\n"
        form_text += " - if favicon is not specified, it is set to domain/favicon.ico\n"
        form_text += "</pre>"

        context["form_description_post"] = form_text

    return ContextData.render(request, "form_basic.html", context)


def add_source_simple(request):
    from ..forms import SourceInputForm
    from ..controllers import SourceDataController

    context = ContextData.get_context(request)
    context["page_title"] += " - add source"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = SourceInputForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]

            ob = SourceDataController.objects.filter(url=url)
            if ob.exists():
                context["form"] = form
                context["source"] = ob[0]

                return ContextData.render(request, "source_edit_exists.html", context)

            data = SourceDataController.get_full_information({"url": url})

            form = SourceForm(initial=data)
            form.method = "POST"
            form.action_url = reverse("{}:source-add".format(ContextData.app_name))
            context["form"] = form

    else:
        form = SourceInputForm()
        form.method = "POST"

        context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def edit_source(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - edit source"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = SourceDataController.objects.filter(id=pk)
    if not ft.exists():
        return ContextData.render(request, "source_edit_does_not_exist.html", context)

    ob = ft[0]

    if request.method == "POST":
        form = SourceForm(request.POST, instance=ob)
        context["form"] = form

        if form.is_valid():
            form.save()

            context["source"] = ob
            return ContextData.render(request, "source_edit_ok.html", context)

        context["summary_text"] = "Could not edit source"

        return ContextData.render(request, "summary_present.html", context)
    else:
        if not ob.favicon:
            from ..webtools import Page

            p = Page(ob.url)

            form = SourceForm(
                instance=ob, initial={"favicon": p.get_domain() + "/favicon.ico"}
            )
        else:
            form = SourceForm(instance=ob)

        form.method = "POST"
        form.action_url = reverse(
            "{}:source-edit".format(ContextData.app_name), args=[pk]
        )
        context["form"] = form
        return ContextData.render(request, "form_basic.html", context)


def refresh_source(request, pk):
    from ..models import SourceOperationalData

    context = ContextData.get_context(request)
    context["page_title"] += " - refresh source"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = SourceDataController.objects.filter(id=pk)
    if not ft.exists():
        return ContextData.render(request, "source_edit_does_not_exist.html", context)

    ob = ft[0]

    operational = SourceOperationalData.objects.filter(url=ob.url)
    if operational.exists():
        op = operational[0]
        op.date_fetched = None
        op.save()

    BackgroundJobController.download_rss(ob, True)

    context["summary_text"] = "Source added to refresh queue"
    return ContextData.render(request, "summary_present.html", context)


def sources_manual_refresh(request):
    from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

    context = ContextData.get_context(request)
    context["page_title"] += " - refresh source"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    objs = SourceDataController.objects.all()

    for ob in objs:
        plugin = SourceControllerBuilder.get(source)
        plugin.check_for_data()

    context["summary_text"] = "Refreshed all sources"
    return ContextData.render(request, "summary_present.html", context)


def remove_source(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove source"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = SourceDataController.objects.filter(id=pk)
    if ft.exists():
        source_url = ft[0].url
        ft.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return ContextData.render(request, "summary_present.html", context)


def source_remove_entries(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove source entries"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = SourceDataController.objects.filter(id=pk)
    if ft.exists():
        entries = LinkDataController.objects.filter(source=ft[0].url)
        if entries.exists():
            entries.delete()
            context["summary_text"] = "Remove ok"
            context["summary_text"] = str(entries)
        else:
            context["summary_text"] = "No entries to remove"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return ContextData.render(request, "summary_present.html", context)


def remove_all_sources(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove all links"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = SourceDataController.objects.all()
    if ft.exists():
        ft.delete()
        context["summary_text"] = "Removing all sources ok"
    else:
        context["summary_text"] = "No source to remove"

    return ContextData.render(request, "summary_present.html", context)


def wayback_save(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Waybacksave"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if ConfigurationEntry.get().source_archive:
        source = SourceDataController.objects.get(id=pk)
        BackgroundJobController.link_archive(subject=source.url)

        context["summary_text"] = "Added to waybacksave"
    else:
        context["summary_text"] = "Waybacksave is disabled for sources"

    return ContextData.render(request, "summary_present.html", context)


def process_source_text(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - process"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    text = """
    """

    from ..pluginsources.rsssourceprocessor import RssSourceProcessor

    source = SourceDataController.objects.get(id=pk)

    proc = RssSourceProcessor()
    proc.process_parser_source(source, text)

    context["summary_text"] = "Added to waybacksave"

    return ContextData.render(request, "summary_present.html", context)


def import_youtube_links_for_source(request, pk):
    from ..programwrappers.ytdlp import YTDLP

    summary_text = ""
    context = ContextData.get_context(request)
    context["page_title"] += " - import sources"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    source_obj = SourceDataController.objects.get(id=pk)

    url = str(source_obj.url)
    wh = url.find("=")

    if wh == -1:
        context["summary_text"] = "Could not obtain code from a video"
        return ContextData.render(request, "summary_present.html", context)

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
        BackgroundJobController.link_add(link, source_obj)

    context["summary_text"] = ""
    return ContextData.render(request, "summary_present.html", context)


def source_fix_entries(request, source_pk):
    from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

    context = ContextData.get_context(request)
    context["page_title"] += " - Update entries for source"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

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

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


def source_json(request, pk):
    sources = SourceDataController.objects.filter(id=pk)

    if len(sources) == 0:
        context["summary_text"] = "No such source in the database {}".format(pk)
        return ContextData.render(request, "summary_present.html", context)

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
