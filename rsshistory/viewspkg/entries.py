from datetime import datetime
import time

from django.views import generic
from django.urls import reverse
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlencode
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt

from utils.dateutils import DateUtils
from utils.omnisearch import SingleSymbolEvaluator
from utils.services import WaybackMachine

from ..webtools import (
    Url,
    UrlLocation,
    RedditUrlHandler,
    GitHubUrlHandler,
    HtmlPage,
    ReturnDislike,
    RemoteServer,
)

from ..apps import LinkDatabase

from ..serializers import entry_to_json

from ..models import (
    BaseLinkDataController,
    BackgroundJob,
    ConfigurationEntry,
    UserConfig,
    UserEntryVisitHistory,
    UserEntryTransitionHistory,
    UserSearchHistory,
    EntryRules,
    UserBookmarks,
    AppLogging,
    SearchView,
)
from ..controllers import (
    DomainsController,
    LinkDataController,
    EntryWrapper,
    EntryDataBuilder,
    ArchiveLinkDataController,
    SourceDataController,
    BackgroundJobController,
    SearchEngines,
    EntryScanner,
    SystemOperationController,
)
from ..forms import (
    EntryForm,
    ConfigForm,
    EntryArchiveForm,
    OmniSearchForm,
    InitSearchForm,
    OmniSearchWithArchiveForm,
    LinkInputForm,
    LinkPropertiesForm,
    AddEntryForm,
)
from ..views import (
    ViewPage,
    get_search_term,
    get_order_by,
    get_page_num,
    get_request_browser,
    get_search_view,
)
from ..queryfilters import EntryFilter, OmniSearchFilter, DjangoEquationProcessor
from ..configuration import Configuration
from ..serializers.instanceimporter import InstanceExporter
from .plugins.entrypreviewbuilder import EntryPreviewBuilder
from ..pluginurl import UrlHandlerEx


def get_generic_search_init_context(request, form):
    context = {}
    context["form"] = form

    search_term = get_search_term(request.GET)

    context["search_term"] = search_term
    context["search_engines"] = SearchEngines(search_term)
    context["view_link"] = form.action_url
    context["form_submit_button_name"] = "🔍"

    context["entry_query_names"] = LinkDataController.get_query_names()
    context["entry_query_operators"] = SingleSymbolEvaluator().get_operators()

    return context


def entries_generic(request, link, data_scope):
    p = ViewPage(request)
    p.set_title("Entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    data = {}
    if "search" in request.GET:
        data = {"search": request.GET["search"]}

    search_view = get_search_view(request)

    # data_scope = "Scope: " + data_scope
    data_scope = "Scope: " + search_view.name

    filter_form = InitSearchForm(
        request=request,
        initial=data,
        scope=data_scope,
        auto_fetch=search_view.auto_fetch,
    )
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries".format(LinkDatabase.name))
    filter_form.auto_fetch = search_view.auto_fetch

    context = get_generic_search_init_context(request, filter_form)

    p.context.update(context)
    p.context["query_page"] = link
    p.context["search_suggestions_page"] = reverse(
        "{}:get-search-suggestions-entries".format(LinkDatabase.name),
        args=["placeholder"],
    )
    p.context["search_history_page"] = reverse(
        "{}:json-user-search-history".format(LinkDatabase.name)
    )

    return p.render("entry_list.html")


def entries(request):
    return entries_generic(
        request, reverse("{}:entries-json".format(LinkDatabase.name)), "all"
    )


def entries_user_bookmarked(request):
    return entries_generic(
        request,
        reverse("{}:entries-json-user-bookmarked".format(LinkDatabase.name)),
        "bookmarked by the user",
    )


def entries_archived(request):
    return entries_generic(
        request,
        reverse("{}:entries-json-archived".format(LinkDatabase.name)),
        "archived",
    )


class EntriesSearchListView(object):

    def __init__(self, request=None, user=None):
        self.request = request
        self.user = user
        self.conditions = None
        self.search_view = None

        if not self.user and self.request and self.request.user:
            self.user = self.request.user

    def get_queryset(self):
        """
        API: Returns queryset
        """
        search_view = self.get_search_view()

        print("EntriesSearchListView:get_queryset")
        self.query_filter = self.get_filter()

        queryset = self.get_filtered_objects().order_by(*self.get_order_by()).distinct()

        if search_view.entry_limit:
            queryset = queryset[: search_view.entry_limit]

        print("EntriesSearchListView:get_queryset done {}".format(queryset.query))

        config = Configuration.get_object().config_entry
        if config.debug_mode:
            self.query = queryset.query

        return queryset

    def get_paginate_by(self):
        """
        API: Returns pagination value
        """
        if not self.user or not self.user.is_authenticated:
            config = Configuration.get_object().config_entry
            return config.links_per_page
        else:
            uc = UserConfig.get(self.user)
            return uc.links_per_page

    def get_order_by(self):
        search_view = self.get_search_view()

        if not search_view:
            return ["-date_published", "link"]

        delimiter = ","
        input_string = search_view.order_by
        result_list = [item.strip() for item in input_string.split(delimiter)]
        return result_list

    def get_search_view(self):
        if self.search_view:
            return self.search_view

        self.search_view = get_search_view(self.request)
        return self.search_view

    def get_filter(self):
        self.on_search()

        search = None
        if "search" in self.request.GET:
            search = self.request.GET["search"]

        query_filter = DjangoEquationProcessor(search)

        translate = BaseLinkDataController.get_query_names()
        query_filter.set_translation_mapping(translate)

        if "archive" in self.request.GET and self.request.GET["archive"] == "on":
            query_filter.set_default_search_symbols(
                [
                    "title__icontains",
                    "link__icontains",
                    "author__icontains",
                    "album__icontains",
                    "description__icontains",
                    # "tags__tag__icontains",
                ]
            )
        else:
            query_filter.set_default_search_symbols(
                [
                    "title__icontains",
                    "link__icontains",
                    "author__icontains",
                    "album__icontains",
                    "description__icontains",
                    "tags__tag__icontains",
                ]
            )

        return query_filter

    def on_search(self):
        if self.user and self.user.is_authenticated:
            search_term = get_search_term(self.request.GET)
            if search_term:
                UserSearchHistory.add(self.user, search_term)

    def get_conditions(self):
        if self.conditions:
            return self.conditions

        self.conditions = (
            self.query_filter.get_conditions() & self.get_search_view_conditions()
        )

        return self.conditions

    def get_search_view_conditions(self):
        search_view = self.get_search_view()
        if not search_view:
            return Q()

        return search_view.get_conditions()

    def get_filtered_objects(self):
        print("EntriesSearchListView:get_filtered_objects")

        if "archive" in self.request.GET and self.request.GET["archive"] == "on":
            query_set = self.get_initial_query_set(archive=True)
        else:
            query_set = self.get_initial_query_set(archive=False)

        conditions = self.get_conditions()

        print("EntriesSearchListView:get_filtered_objects DONE")
        return query_set.filter(conditions)

    def get_initial_query_set(self, archive=False):
        """ """
        if archive:
            return ArchiveLinkDataController.objects.all()
        else:
            return LinkDataController.objects.all()


class UserEntriesBookmarkedListView(EntriesSearchListView):

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        user = self.user

        if user:
            return query_set.filter(bookmarks__user__id=user.id)


class EntriesArchiveListView(EntriesSearchListView):

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET, user=self.user, use_archive=True)
        return query_filter


class EntryDetailView(generic.DetailView):
    model = LinkDataController
    template_name = str(ViewPage.get_full_template("entry_detail.html"))

    def get(self, *args, **kwargs):
        """
        API: Used to redirect if user does not have rights
        """

        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        view = super().get(*args, **kwargs)
        return view

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        self.set_visited()

        return self.setup_context(context)

    def setup_context(self, context):
        object_controller = EntryPreviewBuilder.get(self.object, self.request.user)

        context["page_title"] = self.object.title

        if self.object.description:
            context["page_description"] = self.object.description[:100]

        context["page_thumbnail"] = self.object.thumbnail
        if self.object.date_published:
            context["page_date_published"] = self.object.date_published.isoformat()
        context["object_controller"] = object_controller

        return context

    def set_visited(self):
        user = self.request.user
        if user.is_authenticated:
            from_entry = self.get_from_entry()

            UserEntryVisitHistory.visited(self.object, self.request.user, from_entry)

    def get_from_entry(self):
        from_entry = None
        if "from_entry_id" in self.request.GET:
            from_entry_id = self.request.GET["from_entry_id"]
            entries = LinkDataController.objects.filter(id=from_entry_id)
            if entries.exists():
                from_entry = entries[0]

        return from_entry


class EntryArchivedDetailView(generic.DetailView):
    model = ArchiveLinkDataController
    template_name = str(ViewPage.get_full_template("entry_detail.html"))

    def get(self, *args, **kwargs):
        """
        API: Used to redirect if user does not have rights
        """

        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        view = super().get(*args, **kwargs)
        return view

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        return self.setup_context(context)

    def setup_context(self, context):
        object_controller = EntryPreviewBuilder.get(self.object, self.request.user)

        context["page_title"] = self.object.title

        if self.object.description:
            context["page_description"] = self.object.description[:100]

        context["page_thumbnail"] = self.object.thumbnail
        if self.object.date_published:
            context["page_date_published"] = self.object.date_published.isoformat()
        context["object_controller"] = object_controller

        return context


def get_entry_menu(request, pk):
    p = ViewPage(request)
    p.set_title("Get entry menu")

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    entries = LinkDataController.objects.filter(id=pk)
    if entries.exists():
        entry = entries[0]
        p.context["object"] = entry
        p.context["user"] = request.user
        p.context["object_controller"] = EntryPreviewBuilder.get(
            entry,
            request.user,
        )

    return p.render("entry_detail__buttons.html")


def func_display_empty_form(request, p, template_name):
    form = AddEntryForm(request=request)
    form.method = "POST"

    p.context["form"] = form
    p.context["form_description_post"] = (
        "Internet is dangerous, so carefully select which links you add"
    )

    return p.render(template_name)


def func_display_init_form(request, p, cleaned_link):
    form = LinkInputForm(initial={"link": cleaned_link}, request=request)
    form.method = "POST"

    p.context["form"] = form
    p.context["form_description_post"] = (
        "Internet is dangerous, so carefully select which links you add"
    )

    return p.render("form_basic.html")


def get_cleaned_up_entry_data(request, data):
    link = data["link"]

    data["user"] = request.user
    data["bookmarked"] = True

    page = UrlLocation(link)
    config = Configuration.get_object().config_entry

    if "description" in data:
        data["description"] = LinkDataController.get_description_for_add(
            data["description"]
        )

    return data


def func_display_data_form(request, p, data):
    # TODO remove this
    # or move this code to get-page-properties
    notes = []
    warnings = []
    errors = []

    link = data["link"]

    ob = EntryWrapper(link=link).get()
    if ob:
        return HttpResponseRedirect(ob.get_absolute_url())

    data = get_cleaned_up_entry_data(request, data)

    page = UrlLocation(link)
    config = Configuration.get_object().config_entry

    form = EntryForm(initial=data, request=request)
    form.method = "POST"
    form.action_url = reverse("{}:entry-add-json".format(LinkDatabase.name))
    p.context["form"] = form

    domain = page.get_domain()

    u = UrlHandlerEx(link)

    is_allowed = u.is_allowed()

    # warnings
    if config.prefer_https_links and link.find("http://") >= 0:
        warnings.append(
            "Detected http protocol. Choose https if possible. It is a more secure protocol"
        )
    if config.prefer_non_www_links and domain.find("www.") >= 0:
        warnings.append(
            "Detected www in domain link name. Select non www link if possible"
        )
    if domain.lower() != domain:
        warnings.append("Link domain is not lowercase. Are you sure link name is OK?")
    if not is_allowed:
        warnings.append("Link is not allowed by site robots.txt")
    if link.find("?") >= 0:
        warnings.append("Link contains arguments. Is that intentional?")
    if link.find("#") >= 0:
        warnings.append("Link contains arguments. Is that intentional?")
    if page.get_port() and page.get_port() >= 0:
        warnings.append("Link contains port. Is that intentional?")
    if not page.is_web_link():
        warnings.append(
            "Not a web link. Expecting protocol://domain.tld styled location"
        )

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

    return p.render("form_entry_add.html")


def on_added_entry(request, entry):
    if not entry.is_archive_entry():
        # if you add a link you must have visited it?
        UserEntryVisitHistory.visited(entry, request.user)


def add_entry_json(request):

    from ..controllers import LinkDataController

    p = ViewPage(request)
    p.set_title("Add entry")

    data = {}
    data["pk"] = 0
    data["status"] = False
    data["errors"] = []

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        data["errors"] = ["User is cannot add links"]
    else:
        link = request.GET.get("link", "")
        link = UrlHandlerEx.get_cleaned_link(link)

        if not link or link == "":
            data["errors"] = ["Link is empty"]
            return JsonResponse(data, json_dumps_params={"indent": 4})

        w = EntryWrapper(link=link)
        ob = w.get()
        if ob:
            data["errors"] = ["Entry already is defined"]
        else:
            b = EntryDataBuilder()
            browser = get_request_browser(request.GET)
            entry = b.build_simple(link=link, user=request.user, source_is_auto=False, browser=browser)

            if not entry:
                for error in b.errors:
                    data["errors"].append(f"{error}")
                return JsonResponse(data, json_dumps_params={"indent": 4})

            data["pk"] = entry.id

            if UserBookmarks.add(request.user, entry):
                entry.make_bookmarked()
            if entry.bookmarked:
                entry = EntryWrapper(entry=entry).make_bookmarked(request)

            data["status"] = True

            on_added_entry(request, entry)

    return JsonResponse(data, json_dumps_params={"indent": 4})


def add_simple_entry(request):
    p = ViewPage(request)
    p.set_title("Add entry")

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    return func_display_empty_form(request, p, "entry__add_simple.html")


@csrf_exempt
def entry_add_ext(request):
    p = ViewPage(request)
    p.set_title("Add entry")

    if not p.is_api_key_allowed():
        p.context["summary_text"] = "Cannot add anything"
        return p.render("summary_present.html")

    if request.method == "POST":
        link = request.POST.get("link")
        tag = request.POST.get("tag")

        BackgroundJobController.link_add(link)

        p.context["summary_text"] = "Added link {}".format(link)

        return p.render("summary_present.html")
    else:
        p.context["summary_text"] = "Cannot add anything"
        return p.render("summary_present.html")


def entry_is(request):
    p = ViewPage(request)
    p.set_title("Checks if entry exists")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    link = request.GET["link"]

    data = {}
    wrapper = EntryWrapper(link=link)

    entry = wrapper.get()

    if entry:
        data["status"] = True
        data["pk"] = entry.id
    else:
        data["status"] = False
        data["message"] = "Does not exist"

    return JsonResponse(data, json_dumps_params={"indent": 4})


def entry_update_data(request, pk):
    p = ViewPage(request)
    p.set_title("Update entry data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    entries = LinkDataController.objects.filter(id=pk)
    if not entries.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("summary_present.html")

    else:
        entry = entries[0]
        BackgroundJobController.entry_update_data(entry, force=True)
        return HttpResponseRedirect(entry.get_absolute_url())


def entry_reset_data(request, pk):
    p = ViewPage(request)
    p.set_title("Reset entry data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    entries = LinkDataController.objects.filter(id=pk)
    if not entries.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("summary_present.html")

    else:
        entry = entries[0]
        BackgroundJobController.entry_reset_data(entry, force=True)
        return HttpResponseRedirect(entry.get_absolute_url())


def entry_reset_local_data(request, pk):
    p = ViewPage(request)
    p.set_title("Reset local entry data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    entries = LinkDataController.objects.filter(id=pk)
    if not entries.exists():
        p.context["summary_text"] = "Such entry does not exist: {}".format(pk)
        return p.render("summary_present.html")

    else:
        entry = entries[0]
        BackgroundJobController.entry_reset_local_data(entry)
        return HttpResponseRedirect(entry.get_absolute_url())


def edit_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Edit entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    obs = LinkDataController.objects.filter(id=pk)
    if not obs.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("summary_present.html")

    ob = obs[0]
    if ob.user is None:
        ob.user = request.user
        ob.save()

    if ob.description:
        ob.description = LinkDataController.get_description_for_add(ob.description)
        ob.save()

    if request.method == "POST":
        form = EntryForm(request.POST, instance=ob, request=request)
        p.context["form"] = form

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(ob.get_absolute_url())

        error_message = "\n".join(
            [
                "{}: {}".format(field, ", ".join(errors))
                for field, errors in form.errors.items()
            ]
        )

        p.context["summary_text"] = "Could not edit entry {}".format(error_message)
        return p.render("summary_present.html")
    else:
        form = EntryForm(instance=ob, request=request)
        form.method = "POST"
        form.action_url = reverse("{}:entry-edit".format(LinkDatabase.name), args=[pk])
        p.context["form"] = form
        return p.render("form_basic.html")


def entry_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id=pk)
    status_code = 200

    data = {
        "status": False,
        "message": "",
    }

    if entries.exists():
        for entry in entries:
            entry.delete()

        data["message"] = "Remove ok"
        data["status"] = True
    else:
        data["message"] = "No source for ID: " + str(pk)
        data["status"] = False

    return JsonResponse(data, json_dumps_params={"indent": 4})


def entry_active(request, pk):
    p = ViewPage(request)
    p.set_title("Mark entry as active")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    obj.make_manual_active()

    return HttpResponseRedirect(obj.get_absolute_url())


def entry_dead(request, pk):
    p = ViewPage(request)
    p.set_title("Mark entry as dead")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    obj.make_manual_dead()

    return HttpResponseRedirect(obj.get_absolute_url())


def entry_clear_status(request, pk):
    p = ViewPage(request)
    p.set_title("Clearing entry status")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    obj.clear_manual_status()

    return HttpResponseRedirect(obj.get_absolute_url())


def entry_dislikes(request, pk):
    p = ViewPage(request)
    p.set_title("Show entry likes/dislikes")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    config = Configuration.get_object().config_entry
    if config.remote_webtools_server_location:

        controller = SystemOperationController()
        if controller.is_remote_server_down():
            return JsonResponse({"errors" : ["Remote server is down"]}, json_dumps_params={"indent": 4})

        link = config.remote_webtools_server_location
        remote_server = RemoteServer(link)

        json_obj = remote_server.get_socialj(obj.link)
        if not json_obj:
            return JsonResponse({"errors" : ["Could not obtain social data"]}, json_dumps_params={"indent": 4})

        try:
            return JsonResponse(json_obj, json_dumps_params={"indent": 4})
        except Exception as E:
            return JsonResponse({"errors" : ["Could not dump social data"]}, json_dumps_params={"indent": 4})


def entry_bookmark(request, pk):
    p = ViewPage(request)
    p.set_title("Bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=pk)

    new_entry = EntryWrapper(entry=entry).make_bookmarked(request)

    json_obj = {}

    json_obj["status"] = False
    json_obj["message"] = "Not bookmarked"

    if new_entry:
        if Configuration.get_object().config_entry.enable_link_archiving:
            BackgroundJobController.link_save(entry.link)

        json_obj["status"] = True
        json_obj["message"] = "Bookmarked"

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def entry_unbookmark(request, pk):
    p = ViewPage(request)
    p.set_title("Not bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=pk)
    new_entry = EntryWrapper(entry=entry).make_not_bookmarked(request)

    json_obj = {
        "status": True,
        "message": "Unbookmarked",
    }

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def download_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Download entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    link = LinkDataController.objects.get(id=pk)

    BackgroundJobController.link_download(link_url=link.link)
    summary_text = "Added to queue"

    p.context["summary_text"] = summary_text

    return p.render("go_back.html")


def wayback_save(request, pk):
    p = ViewPage(request)
    p.set_title("Save entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if Configuration.get_object().config_entry.enable_link_archiving:
        link = LinkDataController.objects.get(id=pk)
        BackgroundJobController.link_save(subject=link.link)

        p.context["summary_text"] = "Added to waybacksave"
    else:
        p.context["summary_text"] = "Waybacksave is disabled for links"

    return p.render("go_back.html")


def entry_json(request, pk):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("Remove all entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    links = LinkDataController.objects.filter(id=pk)

    if links.count() == 0:
        p = ViewPage(request)
        p.set_title("Entry JSON")
        p.context["summary_text"] = "No such link in the database {}".format(pk)
        return p.render("summary_present.html")

    link = links[0]

    exporter = InstanceExporter()
    json_obj = exporter.export_link(link)

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def handle_json_view(request, view_to_use):
    page_num = get_page_num(request.GET)

    show_tags = False
    if "tags" in request.GET:
        show_tags = True

    json_obj = {}
    json_obj["entries"] = []
    json_obj["count"] = 0
    json_obj["page"] = page_num
    json_obj["num_pages"] = 0
    json_obj["view"] = None

    start_time = time.time()

    user_config = UserConfig.get(request.user)

    if view_to_use:
        entries = view_to_use.get_queryset()

        json_obj["view"] = view_to_use.get_search_view().name
        json_obj["conditions"] = str(view_to_use.get_conditions())

        p = Paginator(entries, view_to_use.get_paginate_by())
        page_obj = p.get_page(page_num)

        json_obj["count"] = p.count
        json_obj["num_pages"] = p.num_pages

        start = page_obj.start_index()
        if start > 0:
            start -= 1

        if page_num <= p.num_pages:
            for entry in page_obj:
                entry_json = entry_to_json(user_config, entry, tags=show_tags)

                json_obj["entries"].append(entry_json)

        json_obj["timestamp_s"] = time.time() - start_time

        return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def entries_json(request):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    view = EntriesSearchListView(request)

    return handle_json_view(request, view)


def entries_json_recent(request):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    view = EntriesRecentListView(request)

    return handle_json_view(request, view)


def entries_json_bookmarked(request):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    view = EntriesBookmarkedListView(request)

    return handle_json_view(request, view)


def entries_json_user_bookmarked(request):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    view = UserEntriesBookmarkedListView(request)

    return handle_json_view(request, view)


def entries_json_archived(request):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    view = EntriesArchiveListView(request)

    return handle_json_view(request, view)


def entries_json_untagged(request):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    view = EntriesNotTaggedView(request)

    return handle_json_view(request, view)


def entries_remove_all(request):
    p = ViewPage(request)
    p.set_title("Remove all entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    LinkDataController.objects.all().delete()

    p.context["summary_text"] = "Removed all entries"

    return p.render("summary_present.html")


def entries_remove_nonbookmarked(request):
    p = ViewPage(request)
    p.set_title("Remove not bookmarked entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    LinkDataController.objects.filter(bookmarked=False).delete()

    p.context["summary_text"] = "Removed all non bookmarked entries"

    return p.render("summary_present.html")


def archive_make_bookmarked_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = ArchiveLinkDataController.objects.get(id=pk)

    new_entry = EntryWrapper(entry=entry).make_bookmarked(request)

    if new_entry:
        BackgroundJobController.link_save(entry.link)

    return HttpResponseRedirect(new_entry.get_absolute_url())


def archive_make_not_bookmarked_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Not bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=pk)
    new_entry = EntryWrapper(entry=entry).make_not_bookmarked(request)

    return HttpResponseRedirect(new_entry.get_absolute_url())


def archive_edit_entry(request, pk):
    # TODO refactor with edit entry. we do not want copy paste programming
    p = ViewPage(request)
    p.set_title("Edit entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    obs = ArchiveLinkDataController.objects.filter(id=pk)
    if not obs.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("summary_present.html")

    ob = obs[0]
    if ob.user is None or ob.user == "":
        ob.user = str(request.user.username)
        ob.save()

    if request.method == "POST":
        form = EntryArchiveForm(request.POST, instance=ob, request=request)
        context["form"] = form

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(ob.get_absolute_url())

        error_message = "\n".join(
            [
                "{}: {}".format(field, ", ".join(errors))
                for field, errors in form.errors.items()
            ]
        )

        p.context["summary_text"] = "Could not edit entry: {}".format(error_message)

        return p.render("summary_present.html")
    else:
        form = EntryArchiveForm(instance=ob, request=request)
        form.method = "POST"
        form.action_url = reverse(
            "{}:entry-archive-edit".format(LinkDatabase.name), args=[pk]
        )
        p.context["form"] = form
        return p.render("form_basic.html")


def archive_remove_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Remove entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = ArchiveLinkDataController.objects.filter(id=pk)
    if entry.exists():
        entry.delete()

        p.context["summary_text"] = "Remove ok"
    else:
        p.context["summary_text"] = "No source for ID: " + str(pk)

    return p.render("summary_present.html")


def archive_entries_remove_all(request):
    p = ViewPage(request)
    p.set_title("Remove all entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ArchiveLinkDataController.objects.all().delete()

    p.context["summary_text"] = "Removed all entries"

    return p.render("summary_present.html")


def archive_hide_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Hide entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = ArchiveLinkDataController.objects.filter(id=pk)
    obj = objs[0]

    fav = obj.dead
    obj.dead = not obj.dead
    obj.save()

    summary_text = "Link changed to state: " + str(obj.dead)

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def is_entry_download(request, pk):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    is_downloaded = False

    entries = LinkDataController.objects.filter(id=pk)

    if entries.exists():
        entry = entries[0]

        main_condition = Q(subject=entry.id)
        main_condition &= Q(enabled=True)

        job_condition = (
            Q(job=BackgroundJobController.JOB_DOWNLOAD_FILE)
            | Q(job=BackgroundJobController.JOB_LINK_DOWNLOAD_MUSIC)
            | Q(job=BackgroundJobController.JOB_LINK_DOWNLOAD_VIDEO)
        )

        jobs = BackgroundJobController.objects.filter(main_condition & job_condition)
        if jobs.exists():
            is_downloaded = True

    json_obj = {"status": is_downloaded}

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def entry_status(request, pk):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    json_obj = {}

    json_obj["is_downloading"] = False
    json_obj["is_updating"] = False
    json_obj["is_entry"] = False

    entries = LinkDataController.objects.filter(id=pk)

    if entries.exists():
        json_obj["is_entry"] = True

        entry = entries[0]

        main_condition = Q(subject=entry.id)
        main_condition &= Q(enabled=True)

        job_condition = (
            Q(job=BackgroundJobController.JOB_DOWNLOAD_FILE)
            | Q(job=BackgroundJobController.JOB_LINK_DOWNLOAD_MUSIC)
            | Q(job=BackgroundJobController.JOB_LINK_DOWNLOAD_VIDEO)
        )

        jobs = BackgroundJobController.objects.filter(job_condition & main_condition)
        if jobs.exists():
            json_obj["is_downloading"] = True

        job_condition = Q(job=BackgroundJobController.JOB_LINK_UPDATE_DATA)

        jobs = BackgroundJobController.objects.filter(job_condition & main_condition)
        if jobs.exists():
            json_obj["is_updating"] = True

        job_condition = Q(job=BackgroundJobController.JOB_LINK_RESET_DATA)

        jobs = BackgroundJobController.objects.filter(job_condition & main_condition)
        if jobs.exists():
            json_obj["is_resetting"] = True

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def entry_parameters(request, pk):
    p = ViewPage(request)
    p.set_title("Entry parameters")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id = pk)
    if not entries.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("go_back.html")

    entry = entries[0]

    json_obj = {}
    json_obj["parameters"] = []
    
    object_controller = EntryPreviewBuilder.get(entry, request.user)
    for parameter in object_controller.get_parameters():
        adict = {}

        adict["name"] = parameter.name
        adict["title"] = parameter.title
        adict["description"] = parameter.description

        json_obj["parameters"].append(adict)

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def entry_op_parameters(request, pk):
    p = ViewPage(request)
    p.set_title("Entry parameters")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id = pk)
    if not entries.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("go_back.html")

    entry = entries[0]

    json_obj = {}
    json_obj["parameters"] = []
    
    object_controller = EntryPreviewBuilder.get(entry, request.user)
    for parameter in object_controller.get_parameters_operation():
        adict = {}

        adict["name"] = parameter.name
        adict["title"] = parameter.title
        adict["description"] = parameter.description

        json_obj["parameters"].append(adict)

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


def entry_related(request, pk):
    p = ViewPage(request)
    p.set_title("Entry related")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id = pk)
    if not entries.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("go_back.html")

    entry = entries[0]

    config = Configuration.get_object().config_entry
    if config.track_user_actions and config.track_user_navigation:
        p.context["transitions"] = UserEntryTransitionHistory.get_related_list(
            request.user, entry
        )

    return p.render("entry_detail__related.html")


def entry_related_json(request, pk):
    p = ViewPage(request)
    p.set_title("Entry related")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    entries = LinkDataController.objects.filter(id = pk)
    if not entries.exists():
        p.context["summary_text"] = "Such entry does not exist"
        return p.render("go_back.html")

    entry_main = entries[0]
    json_obj = {}

    show_tags = False
    if "tags" in request.GET:
        show_tags = True

    json_obj["entries"] = []

    user_config = UserConfig.get(request.user)

    config = Configuration.get_object().config_entry
    if config.track_user_actions and config.track_user_navigation:
        entries = UserEntryTransitionHistory.get_related_list(request.user, entry_main)

        for entry in entries:
            entry_json = entry_to_json(user_config, entry, tags=show_tags)

            json_obj["entries"].append(entry_json)

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})
