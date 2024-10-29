from pathlib import Path

from django.views import generic
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlencode
from django.core.paginator import Paginator

from ..webtools import Url, DomainAwarePage, HttpPageHandler, DomainCache
from utils.omnisearch import SingleSymbolEvaluator

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    UserConfig,
    AppLogging,
    SourceCategories,
    EntryRules,
)
from ..controllers import (
    SourceDataController,
    SourceDataBuilder,
    EntryDataBuilder,
    LinkDataController,
    BackgroundJobController,
    EntryWrapper,
    SearchEngines,
)
from ..forms import SourceForm, ContentsForm, SourcesChoiceForm, SourceInputForm
from ..queryfilters import SourceFilter
from ..views import ViewPage, GenericListView, get_page_num, get_search_term
from ..configuration import Configuration
from ..pluginurl import UrlHandler
from ..pluginsources import SourceControllerBuilder
from ..serializers import InstanceExporter, JsonImporter


class SourceListView(object):
    def __init__(self, request=None):
        self.request = request

    def get_queryset(self):
        self.query_filter = SourceFilter(self.request.GET, self.request.user, init_objects = self.get_init_query_set())
        return self.query_filter.get_filtered_objects()

    def get_init_query_set(self):
        return SourceDataController.objects.all()

    def get_paginate_by(self):
        if not self.request.user.is_authenticated:
            config = Configuration.get_object().config_entry
            return config.sources_per_page
        else:
            uc = UserConfig.get(self.request.user)
            return uc.sources_per_page

    def get_title(self):
        return "Sources"


class SourcesEnabledListView(SourceListView):
    def get_init_query_set(self):
        return SourceDataController.objects.filter(enabled=True)


class SourceDetailView(generic.DetailView):
    model = SourceDataController

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        handler = UrlHandler(self.object.url)

        context["page_title"] = self.object.title
        context["page_thumbnail"] = self.object.favicon
        context["search_engines"] = SearchEngines(self.object.title, self.object.url)
        context["page_handler"] = handler.get_handler()

        ViewPage.fill_context_type(context, urlhandler=handler)

        c = Configuration.get_object()
        if hasattr(self.object, "dynamic_data"):
            context["date_fetched"] = c.get_local_time(
                self.object.dynamic_data.date_fetched
            )

        entries = LinkDataController.objects.filter(link=self.object.url)
        if entries.count() > 0:
            context["entry_object"] = entries[0]
        else:
            AppLogging.error("Missing source entry {}".format(self.object.url))
            builder = EntryDataBuilder(link=self.object.url)
            if builder.result:
                entry = builder.result
                if entry.is_archive_entry():
                    entry = EntryWrapper(entry=entry).move_from_archive()

                entry.permanent = True
                entry.save()

                context["entry_object"] = entry

        ViewPage.fill_context_type(context, url=self.object.url)

        context["handler"] = SourceControllerBuilder.get(self.object.id)

        return context


def get_generic_search_init_context(request, form, user_choices):
    context = {}
    context["form"] = form

    search_term = get_search_term(request.GET)
    context["search_term"] = search_term
    context["search_engines"] = SearchEngines(search_term)
    context["search_history"] = user_choices
    context["view_link"] = form.action_url
    context["form_submit_button_name"] = "Search"

    context["entry_query_names"] = SourceDataController.get_query_names()
    context["entry_query_operators"] = SingleSymbolEvaluator().get_operators()

    return context


def sources(request):
    p = ViewPage(request)
    p.set_title("Sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    data = {}
    if "search" in request.GET:
        data={"search": request.GET["search"]}

    filter_form = SourcesChoiceForm(request=request, initial=data)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:sources".format(LinkDatabase.name))

    # TODO jquery that
    #user_choices = UserSearchHistory.get_user_choices(request.user)
    user_choices = []
    context = get_generic_search_init_context(request, filter_form, user_choices)

    p.context.update(context)
    p.context["query_page"] = reverse("{}:sources-json-all".format(LinkDatabase.name))

    p.context["search_suggestions_page"] = reverse("{}:get-search-suggestions-sources".format(LinkDatabase.name), args=["placeholder"])
    p.context["search_history_page"] = None

    return p.render("sources_list.html")


def add_source(request):
    p = ViewPage(request)
    p.set_title("Add source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    if request.method == "POST":
        method = "POST"

        form = SourceForm(request.POST, request=request)

        if form.is_valid():
            sources = SourceDataController.objects.filter(url=form.cleaned_data["url"])
            if sources.count() > 0:
                return HttpResponseRedirect(source.get_absolute_url())

            b = SourceDataBuilder(manual_entry=True)
            b.link_data = form.cleaned_data
            b.manual_entry = True
            source = b.build_from_props()

            if not source:
                p.context["summary_text"] = "Cannot add source"
                return p.render("go_back.html")

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
        form = SourceForm(request=request)
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
    def get_add_link_form(p, url):
        url = UrlHandler.get_cleaned_link(url)

        if not Url.is_protocolled_link(url):
            p.context["summary_text"] = "Only protocolled links are allowed. Link:{}".format(
                url
            )
            return p.render("summary_present.html")

        ob = SourceDataController.objects.filter(url=url)
        if ob.exists():
            p.context["form"] = form
            p.context["source"] = ob[0]

            return HttpResponseRedirect(ob[0].get_absolute_url())

        data = SourceDataController.get_full_information({"url": url})
        if not data:
            p.context["summary_text"] = "Could not obtain properties of link:{}".format(
                url
            )
            return p.render("summary_present.html")

        notes = []
        warnings = []
        errors = []

        form = SourceForm(initial=data, request=request)
        form.method = "POST"
        form.action_url = reverse("{}:source-add".format(LinkDatabase.name))

        p.context["form"] = form

        link = data["url"]

        page = DomainAwarePage(data["url"])
        domain = page.get_domain()
        config = Configuration.get_object().config_entry
        info = DomainCache.get_object(link, url_builder=UrlHandler)

        # warnings
        if config.prefer_https and link.find("http://") >= 0:
            warnings.append(
                "Detected http protocol. Choose https if possible. It is a more secure protocol"
            )
        if config.prefer_non_www_sites and domain.find("www.") >= 0:
            warnings.append(
                "Detected www in domain link name. Select non www link if possible"
            )
        if domain.lower() != domain:
            warnings.append("Link domain is not lowercase. Are you sure link name is OK?")
        if config.respect_robots_txt and info and not info.is_allowed(link):
            warnings.append("Link is not allowed by site robots.txt")
        if link.find("?") >= 0:
            warnings.append("Link contains arguments. Is that intentional?")
        if link.find("#") >= 0:
            warnings.append("Link contains arguments. Is that intentional?")
        if page.get_protocolless().find(":") >= 0:
            warnings.append("Link contains port. Is that intentional?")
        if not page.is_web_link():
            warnings.append("Not a web link. Expecting protocol://domain.tld styled location")

        # errors
        if not page.is_protocolled_link():
            errors.append("Not a protocolled link. Forget http:// or https:// etc.?")
        if data["status_code"] < 200 or data["status_code"] > 300:
            errors.append("Information about page availability could not be obtained")
        if EntryRules.is_blocked(link):
            errors.append("Entry is blocked by entry rules")

        p.context["form_notes"] = notes
        p.context["form_warnings"] = warnings
        p.context["form_errors"] = errors

        return p.render("form_source_add.html")

    p = ViewPage(request)
    p.set_title("Add source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    if request.method == "POST":
        form = SourceInputForm(request.POST, request=request)
        if form.is_valid():
            url = form.cleaned_data["url"]

            return get_add_link_form(p, url)

        p.context["form"] = form
    elif request.method == "GET" and "link" in request.GET:
        return get_add_link_form(p, request.GET["link"])

    form = SourceInputForm(request=request)
    form.method = "POST"

    p.context["form"] = form

    return p.render("form_source_add_simple.html")


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
        form = SourceForm(request.POST, instance=ob, request=request)
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
            icon = UrlHandler(ob.url).get_thumbnail()

            if not icon:
                page = DomainAwarePage(ob.url)
                domain = page.get_domain()
                u = UrlHandler(domain, handler_class=HttpPageHandler)
                icon = u.get_favicon()

            if icon:
                form = SourceForm(
                    instance=ob, initial={"favicon": icon}, request=request
                )
            else:
                form = SourceForm(instance=ob, request=request)
        else:
            form = SourceForm(instance=ob, request=request)

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

    for ob in objs:
        plugin = SourceControllerBuilder.get(ob.id)
        plugin.check_for_data()

    return HttpResponseRedirect(reverse("{}:sources".format(LinkDatabase.name)))


def remove_source(request, pk):
    p = ViewPage(request)
    p.set_title("Remove source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    sources = SourceDataController.objects.filter(id=pk)
    if sources.exists():
        for source in sources:
            source.custom_remove()

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

    sources = SourceDataController.objects.all()
    if sources.exists():
        for source in sources:
            source.custom_remove()

        return HttpResponseRedirect(reverse("{}:sources".format(LinkDatabase.name)))
    else:
        p.context["summary_text"] = "No source to remove"

    return p.render("summary_present.html")


def enable_all_sources(request):
    p = ViewPage(request)
    p.set_title("Enable all sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    sources = SourceDataController.objects.filter(enabled=False)
    if sources.exists():
        for source in sources:
            source.enable()

        return HttpResponseRedirect(reverse("{}:sources".format(LinkDatabase.name)))
    else:
        p.context["summary_text"] = "No source to remove"


def disable_all_sources(request):
    p = ViewPage(request)
    p.set_title("Disable all sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    sources = SourceDataController.objects.filter(enabled=True)
    if sources.exists():
        for source in sources:
            source.disable()

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


def disable(request, pk):
    p = ViewPage(request)
    p.set_title("Disable source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    sources = SourceDataController.objects.filter(id=pk)
    if not sources.exists():
        p.context["summary_text"] = "Source does not exist"
        return p.render("summary_present.html")

    ob = sources[0]
    ob.enabled = False
    ob.save()

    return HttpResponseRedirect(ob.get_absolute_url())


def enable(request, pk):
    p = ViewPage(request)
    p.set_title("Enable source")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    sources = SourceDataController.objects.filter(id=pk)
    if not sources.exists():
        p.context["summary_text"] = "Source does not exist"
        return p.render("summary_present.html")

    ob = sources[0]
    ob.enabled = True
    ob.save()

    return HttpResponseRedirect(ob.get_absolute_url())


def source_process_contents(request, pk):
    p = ViewPage(request)
    p.set_title("Source process contents")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    sources = SourceDataController.objects.filter(id=pk)
    if not sources.exists():
        p.context["summary_text"] = "Source does not exist"
        return p.render("summary_present.html")

    source = sources[0]

    if request.method == "POST":
        form = ContentsForm(request.POST, request=request)

        if form.is_valid():
            source_text = form.cleaned_data["body"]
            plugin = SourceControllerBuilder.get(pk)
            plugin.contents = source_text
            plugin.check_for_data()

            p.context["summary_text"] = "Processed"
            return p.render("summary_present.html")
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")
    else:
        form = ContentsForm(request=request)
        form.method = "POST"
        p.context["form"] = form

        return p.render("form_basic.html")


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
        wrapper = EntryWrapper(link=link)
        if not wrapper.get():
            BackgroundJobController.link_add(link, source=source_obj, user=request.user)

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
        if not entry.source:
            entry.source = source_obj
            entry.save()
            summary_text += "Fixed {} {}\n".format(entry.title, entry.link)

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def init_sources(request):
    if "noinitialize" not in request.GET:
        path = Path("init_sources.json")
        if path.exists():
            i = JsonImporter(path)
            i.import_all()


def sources_initialize(request):
    p = ViewPage(request)
    p.set_title("Initialize sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    init_sources(request)

    return redirect("{}:sources".format(LinkDatabase.name))


def source_json(request, pk):
    p = ViewPage(request)
    p.set_title("Remove all entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    sources = SourceDataController.objects.filter(id=pk)

    if sources.count() == 0:
        p = ViewPage(request)
        p.set_title("Source JSON")
        p.context["summary_text"] = "No such source in the database {}".format(pk)
        return p.render("summary_present.html")

    source = sources[0]

    exporter = InstanceExporter()
    json_obj = exporter.export_source(source)

    # JsonResponse
    return JsonResponse(json_obj)


def source_to_json(user_config, source):
    json_source = {}
    json_source["id"] = source.id
    json_source["title"] = source.title
    json_source["url"] = source.url
    json_source["url_absolute"] = source.get_absolute_url()
    json_source["favicon"] = source.favicon
    json_source["enabled"] = source.enabled
    json_source["errors"] = 0
    if hasattr(source, "dynamic_data"):
        if source.dynamic_data:
            json_source["errors"] = source.dynamic_data.consecutive_errors

    return json_source


def sources_json_view(request, view_class):
    p = ViewPage(request)
    p.set_title("Returns all sources JSON")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    page_num = p.get_page_num()

    json_obj = {}
    json_obj["sources"] = []
    json_obj["count"] = 0
    json_obj["page"] = page_num
    json_obj["num_pages"] = 0

    view = view_class(request)

    uc = UserConfig.get(request.user)

    sources = view.get_queryset()
    p = Paginator(sources, view.get_paginate_by())
    page_obj = p.get_page(page_num)

    json_obj["count"] = p.count
    json_obj["num_pages"] = p.num_pages

    start = page_obj.start_index()
    if start > 0:
        start -= 1

    limited_sources = sources[start : page_obj.end_index()]

    for source in limited_sources:
        source_json = source_to_json(uc, source)

        json_obj["sources"].append(source_json)

    # JsonResponse
    return JsonResponse(json_obj)


def sources_json_all(request):
    return sources_json_view(request, SourceListView)


def sources_json_enabled(request):
    return sources_json_view(request, SourcesEnabledListView)


def categories_view(request):
    p = ViewPage(request)
    p.set_title("Source categories")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    categories = SourceCategories.objects.all()

    p.context["categories"] = categories

    return p.render("categories_list.html")


def categories_reset(request):
    p = ViewPage(request)
    p.set_title("Reset Source categories")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    SourceDataController.reset_dynamic_data()

    return redirect("{}:sources".format(LinkDatabase.name))
