from datetime import datetime

from django.views import generic
from django.urls import reverse
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlencode
from django.core.paginator import Paginator

from ..webtools import Url, DomainAwarePage, DomainCache
from utils.dateutils import DateUtils
from utils.serializers import ReturnDislike
from utils.omnisearch import SingleSymbolEvaluator
from utils.services import WaybackMachine

from ..apps import LinkDatabase
from ..models import (
    BaseLinkDataController,
    BackgroundJob,
    ConfigurationEntry,
    UserConfig,
    Domains,
    UserEntryVisitHistory,
    UserEntryTransitionHistory,
    UserSearchHistory,
    EntryRules,
    UserBookmarks,
)
from ..controllers import (
    LinkDataController,
    EntryWrapper,
    EntryDataBuilder,
    ArchiveLinkDataController,
    SourceDataController,
    BackgroundJobController,
    SearchEngines,
    EntryScanner,
)
from ..forms import (
    EntryForm,
    ConfigForm,
    EntryArchiveForm,
    OmniSearchForm,
    InitSearchForm,
    OmniSearchWithArchiveForm,
    LinkInputForm,
)
from ..views import (
    ViewPage,
    get_search_term,
    get_order_by,
    get_page_num,
)
from ..queryfilters import EntryFilter, OmniSearchFilter
from ..configuration import Configuration
from ..pluginurl import UrlHandler
from ..serializers.instanceimporter import InstanceExporter
from .plugins.entrypreviewbuilder import EntryPreviewBuilder


def get_query_args(themap):
    """
    display type is not required
    search is added by filter form, so we do not want it to be here

    # TODO - add argument, to pass all keys that should be rejected
    """
    arg_data = {}
    for arg in themap:
        if arg == "display_type":
            continue
        if arg == "search":
            continue

        arg_data[arg] = themap[arg]

    return "&" + urlencode(arg_data)


def get_generic_search_init_context(request, form, user_choices):
    context = {}
    context["form"] = form

    search_term = get_search_term(request.GET)
    context["search_term"] = search_term
    context["search_engines"] = SearchEngines(search_term)
    context["search_history"] = user_choices
    context["view_link"] = form.action_url
    context["form_submit_button_name"] = "Search"

    context["entry_query_names"] = LinkDataController.get_query_names()
    context["entry_query_operators"] = SingleSymbolEvaluator().get_operators()

    return context


def entries_generic(request, link):
    p = ViewPage(request)
    p.set_title("Entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    data = {}
    if "search" in request.GET:
        data={"search": request.GET["search"]}

    filter_form = InitSearchForm(request=request, initial=data)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries".format(LinkDatabase.name))

    # TODO jquery that
    user_choices = UserSearchHistory.get_user_choices(request.user)
    context = get_generic_search_init_context(request, filter_form, user_choices)

    p.context.update(context)
    p.context["query_args"] = get_query_args(request.GET)
    p.context["query_page"] = link

    return p.render("entries.html")


def entries(request):
    return entries_generic(request, reverse("{}:get-entries".format(LinkDatabase.name)))


def entries_recent(request):
    return entries_generic(request, reverse("{}:get-entries-recent".format(LinkDatabase.name)))


def entries_bookmarked(request):
    return entries_generic(request, reverse("{}:get-entries-bookmarked".format(LinkDatabase.name)))


def entries_user_bookmarked(request):
    return entries_generic(request, reverse("{}:get-entries-user-bookmarked".format(LinkDatabase.name)))


def entries_archived(request):
    return entries_generic(request, reverse("{}:get-entries-archived".format(LinkDatabase.name)))


def entries_untagged(request):
    return entries_generic(request, reverse("{}:get-entries-untagged".format(LinkDatabase.name)))

    return p.render("entries.html")


class EntriesSearchListView(generic.ListView):
    model = LinkDataController
    context_object_name = "entry_list"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("linkdatacontroller_list__dynamic.html"))

    def get(self, *args, **kwargs):
        """
        API: Used to redirect if user does not have rights
        """
        print("EntriesSearchListView:get")

        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        self.time_start = datetime.now()
        self.query = None

        print("EntriesSearchListView:get constructor of list view")
        view = super().get(*args, **kwargs)
        print("EntriesSearchListView:get done")
        return view

    def get_queryset(self):
        """
        API: Returns queryset
        """
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        print("EntriesSearchListView:get_queryset")
        self.query_filter = self.get_filter()
        objects = self.get_filtered_objects().order_by(*self.get_order_by())
        print("EntriesSearchListView:get_queryset done {}".format(objects.query))

        config = Configuration.get_object().config_entry
        if config.debug_mode:
            self.query = objects.query

        return objects

    def get_paginate_by(self, queryset):
        """
        API: Returns pagination value
        """
        if not self.request.user.is_authenticated:
            config = Configuration.get_object().config_entry
            return config.links_per_page
        else:
            uc = UserConfig.get(self.request.user)
            return uc.links_per_page

    def get_context_data(self, **kwargs):
        """
        API:
        """
        print("EntriesSearchListView:get_context_data")
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)

        context = ViewPage(self.request).init_context(context)
        # Create any data and add it to the context
        self.init_display_type(context)

        self.search_term = get_search_term(self.request.GET)

        context["query_filter"] = self.query_filter
        context["view_link"] = self.get_view_link()

        context["query_type"] = self.get_query_type()
        context["query"] = self.query

        context["search_engines"] = SearchEngines(self.search_term)
        context["form_submit_button_name"] = "Search"

        if Url.is_protocolled_link(self.search_term):
            context["search_query_add"] = self.search_term

        print(
            "EntriesSearchListView:get_context_data done. View time delta:{}".format(
                datetime.now() - self.time_start
            )
        )

        return context

    def get_order_by(self):
        return get_order_by(self.request.GET)

    def get_filter(self):
        print("EntriesSearchListView:get_filter")

        query_filter = EntryFilter(self.request.GET, self.request.user)
        thefilter = query_filter
        print("EntriesSearchListView:get_filter done")
        return thefilter

    def get_filtered_objects(self):
        print("EntriesSearchListView:get_filtered_objects")
        return self.query_filter.get_filtered_objects()

    def get_reset_link(self):
        return reverse("{}:entries".format(LinkDatabase.name))

    def get_view_link(self):
        return reverse("{}:entries".format(LinkDatabase.name))

    def has_more_results(self):
        return True

    def get_more_results_link(self):
        return (
            reverse("{}:entries".format(LinkDatabase.name))
            + "?"
            + self.query_filter.get_filter_string()
        )

    def get_search_link(self, search_term):
        if search_term.find("link =") >= 0 or search_term.find("link=") >= 0:
            wh = search_term.find("=")
            if wh >= 0:
                wh2 = search_term.find("=", wh + 1)
                if wh2 >= 0:
                    wh = wh2

                search_term = search_term[wh + 1 :].strip()

        return search_term

    def get_title(self):
        return " - entries {}".format(self.search_term)

    def get_query_type(self):
        return "standard"

    def init_display_type(self, context):
        # TODO https://stackoverflow.com/questions/57487336/change-value-for-paginate-by-on-the-fly
        # if type is not normal, no pagination
        if "display_type" in self.request.GET:
            context["display_type"] = self.request.GET["display_type"]
        else:
            context["display_type"] = "normal"
        context["query_args"] = get_query_args(self.request.GET)

    def get_default_range(self):
        config = Configuration.get_object().config_entry
        return DateUtils.get_days_range(config.whats_new_days)


class EntriesOmniListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "entry_list"
    paginate_by = 100

    def get_filter(self):
        self.on_search()

        query_filter = OmniSearchFilter(self.request.GET)

        translate = BaseLinkDataController.get_query_names()
        query_filter.set_translation_mapping(translate)

        if "archive" in self.request.GET and self.request.GET["archive"] == "on":
            query_filter.set_default_search_symbols(
                [
                    "title__icontains",
                    "link__icontains",
                    "artist__icontains",
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
                    "artist__icontains",
                    "album__icontains",
                    "description__icontains",
                    "tags__tag__icontains",
                ]
            )

        query_filter.get_conditions()

        return query_filter

    def on_search(self):
        if self.request.user.is_authenticated:
            search_term = get_search_term(self.request.GET)
            if search_term:
                UserSearchHistory.add(self.request.user, search_term)

    def get_filtered_objects(self):
        fields = self.query_filter.get_not_translated_conditions()

        if ("archive" in self.request.GET and self.request.GET["archive"] == "on") or (
            "archive" in fields and fields["archive"] == "1"
        ):
            query_set = self.get_initial_query_set(archive=True)
        else:
            query_set = self.get_initial_query_set(archive=False)

        self.query_filter.set_query_set(query_set)

        return self.query_filter.get_filtered_objects()

    def get_initial_query_set(self, archive=False):
        """
        TODO rewrite. Filter should return only query sets. pure. without pagination
        """
        if archive:
            return ArchiveLinkDataController.objects.all()
        else:
            return LinkDataController.objects.all()

    def get_reset_link(self):
        return reverse("{}:entries".format(LinkDatabase.name))

    def get_view_link(self):
        return reverse("{}:entries".format(LinkDatabase.name))

    def has_more_results(self):
        if "archive" in self.request.GET:
            return False
        else:
            return True

    def get_more_results_link(self):
        if "search" in self.request.GET:
            return reverse(
                "{}:entries".format(LinkDatabase.name)
            ) + "?archive=on&search={}".format(self.request.GET["search"])
        else:
            return (
                reverse("{}:entries".format(LinkDatabase.name))
                + "?archive=on"
            )

    def get_query_type(self):
        return "omni"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class EntriesRecentListView(EntriesOmniListView):
    model = LinkDataController
    context_object_name = "entry_list"
    paginate_by = 100

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        return query_set.filter(date_published__range=self.get_default_range())

    def get_order_by(self):
        return ["-date_published"]

    def get_reset_link(self):
        return reverse("{}:entries-recent-init".format(LinkDatabase.name))

    def get_view_link(self):
        return reverse("{}:entries-recent".format(LinkDatabase.name))

    def get_title(self):
        return " - entries {}".format(self.search_term)

    def get_query_type(self):
        return "recent"


class EntriesNotTaggedView(EntriesOmniListView):
    model = LinkDataController
    context_object_name = "entry_list"
    paginate_by = 100

    def get_order_by(self):
        return ["-date_published"]

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        tags_is_null = Q(tags__isnull=True)
        bookmarked = Q(bookmarked=True)
        permanent = Q(permanent=True)
        return query_set.filter(tags_is_null & (bookmarked | permanent))

    def has_more_results(self):
        return False

    def get_reset_link(self):
        return reverse("{}:entries-untagged".format(LinkDatabase.name))

    def get_view_link(self):
        return reverse("{}:entries-untagged".format(LinkDatabase.name))

    def get_title(self):
        return " - entries {}".format(self.search_term)

    def get_query_type(self):
        return "not-tagged"


class EntriesBookmarkedListView(EntriesOmniListView):
    model = LinkDataController
    context_object_name = "entry_list"
    paginate_by = 100

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        return query_set.filter(bookmarked=1)

    def has_more_results(self):
        return False

    def get_reset_link(self):
        return reverse("{}:entries-bookmarked-init".format(LinkDatabase.name))

    def get_view_link(self):
        return reverse("{}:entries-bookmarked".format(LinkDatabase.name))

    def get_title(self):
        return " - entries {}".format(self.search_term)

    def get_query_type(self):
        return "bookmarked"


class UserEntriesBookmarkedListView(EntriesOmniListView):
    model = LinkDataController
    context_object_name = "entry_list"
    paginate_by = 100

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        user = self.request.user
        return query_set.filter(bookmarks__user__id=user.id)

    def has_more_results(self):
        return False

    def get_reset_link(self):
        return reverse("{}:entries-user-bookmarked".format(LinkDatabase.name))

    def get_view_link(self):
        return reverse("{}:entries-user-bookmarked".format(LinkDatabase.name))

    def get_title(self):
        return " - entries {}".format(self.search_term)

    def get_query_type(self):
        return "bookmarked"


class EntriesArchiveListView(EntriesOmniListView):
    model = LinkDataController
    context_object_name = "entry_list"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("linkdatacontroller_list.html"))

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET, self.request.user)
        query_filter.set_archive_source(True)
        return query_filter

    def has_more_results(self):
        return False

    def get_reset_link(self):
        return reverse("{}:entries-archived-init".format(LinkDatabase.name))

    def get_view_link(self):
        return reverse("{}:entries-archived".format(LinkDatabase.name))

    def get_title(self):
        return " - entries {}".format(self.search_term)

    def get_query_type(self):
        return "archived"


class EntryDetailView(generic.DetailView):
    model = LinkDataController
    template_name = str(ViewPage.get_full_template("linkdatacontroller_detail.html"))

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
        if self.request.user.is_authenticated:
            BackgroundJobController.entry_update_data(self.object)
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


class EntryDetailDetailView(generic.DetailView):
    model = LinkDataController
    template_name = str(ViewPage.get_full_template("linkdatacontroller_detail__dynamic.html"))

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

        context["object_controller"] = object_controller

        config = Configuration.get_object().config_entry
        if config.track_user_actions and config.track_user_navigation:
            context["transitions"] = UserEntryTransitionHistory.get_related_list(
                self.request.user, self.object
            )

        m = WaybackMachine()
        context["search_engines"] = SearchEngines(
            self.object.get_search_term(), self.object.link
        )

        return context


class EntryArchivedDetailView(generic.DetailView):
    model = ArchiveLinkDataController

    template_name = str(ViewPage.get_full_template("linkdatacontroller_detail.html"))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        if self.object.language == None:
            self.object.update_language()

        context["page_title"] = self.object.title
        context["page_thumbnail"] = self.object.thumbnail
        context["object_controller"] = EntryPreviewBuilder.get(
            self.object, self.request.user
        )

        m = WaybackMachine()
        context["archive_org_date"] = m.get_formatted_date(DateUtils.get_date_today())

        return context

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


def func_display_empty_form(request, p, template_name):
    form = LinkInputForm(request=request)
    form.method = "POST"

    p.context["form"] = form
    p.context[
        "form_description_post"
    ] = "Internet is dangerous, so carefully select which links you add"

    return p.render(template_name)


def func_display_init_form(request, p, cleaned_link):
    form = LinkInputForm(initial={"link": cleaned_link}, request=request)
    form.method = "POST"

    p.context["form"] = form
    p.context[
        "form_description_post"
    ] = "Internet is dangerous, so carefully select which links you add"

    return p.render("form_basic.html")


def func_display_data_form(request, p, data):
    notes = []
    warnings = []
    errors = []

    link = data["link"]

    ob = EntryWrapper(link=link).get()
    if ob:
        return HttpResponseRedirect(ob.get_absolute_url())

    data["user"] = request.user
    data["bookmarked"] = True

    if "description" in data:
        data["description"] = LinkDataController.get_description_for_add(
            data["description"]
        )

    form = EntryForm(initial=data, request=request)
    form.method = "POST"
    form.action_url = reverse("{}:entry-add".format(LinkDatabase.name))
    p.context["form"] = form

    page = DomainAwarePage(link)
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

    return p.render("form_entry_add.html")


def add_entry(request):
    def on_added_entry(request, entry):
        # if you add a link you must have visited it?
        UserEntryVisitHistory.visited(entry, request.user)

        BackgroundJobController.link_scan(entry=entry)

        if entry.bookmarked:
            new_entry = EntryWrapper(entry=entry).make_bookmarked(request)

        config = Configuration.get_object().config_entry

        if config.link_save:
            BackgroundJobController.link_save(entry.link)

    from ..controllers import LinkDataController

    p = ViewPage(request)
    p.set_title("Add entry")

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = EntryForm(request.POST, request=request)

        # check whether it's valid:
        valid = form.is_valid()
        link = request.POST.get("link", "")

        w = EntryWrapper(link=link)
        ob = w.get()
        if ob:
            return HttpResponseRedirect(ob.get_absolute_url())

        if valid:
            data = form.get_information()

            b = EntryDataBuilder()
            b.link_data = data
            b.source_is_auto = False
            b.user = request.user
            entry = b.build_from_props_internal()

            if not entry:
                p.context["summary_text"] = "Link was not saved"
                return p.render("summary_present.html")

            p.context["entry"] = entry
            p.context["form"] = form

            on_added_entry(request, entry)

            return p.render("entry_added.html")

        error_message = "\n".join(
            [
                "{}: {}".format(field, ", ".join(errors))
                for field, errors in form.errors.items()
            ]
        )

        p.context["summary_text"] = "Form is invalid: {}".format(error_message)
        return p.render("summary_present.html")

    else:
        if "link" in request.GET:
            link = request.GET["link"]

            link = UrlHandler.get_cleaned_link(link)

            if not Url.is_protocolled_link(link):
                p.context[
                    "summary_text"
                ] = "Only protocolled links are allowed. Link:{}".format(link)
                return p.render("summary_present.html")

            data = LinkDataController.get_full_information({"link": link})
            if data:
                return func_display_data_form(request, p, data)

            p.context["summary_text"] = "Could not obtain details from link {}".format(
                link
            )
            return p.render("go_back.html")

        return func_display_empty_form(request, p, "form_entry_add.html")


def add_simple_entry(request):
    p = ViewPage(request)
    p.set_title("Add entry")

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    if request.method == "POST":
        form = LinkInputForm(request.POST, request=request)
        if form.is_valid():
            link = form.cleaned_data["link"]

            cleaned_link = UrlHandler.get_cleaned_link(link)

            if cleaned_link != link:
                return func_display_init_form(request, p, cleaned_link)

            if not Url.is_protocolled_link(link):
                p.context[
                    "summary_text"
                ] = "Only protocolled links are allowed. Link:{}".format(link)
                return p.render("summary_present.html")

            data = LinkDataController.get_full_information({"link": link})
            if data:
                return func_display_data_form(request, p, data)

            p.context["summary_text"] = "Could not obtain details from link {}".format(
                link
            )
            return p.render("go_back.html")

        else:
            p.context["summary_text"] = "Form is invalid {}".format(link)
            return p.render("summary_present.html")
    else:
        return func_display_empty_form(request, p, "form_entry_add_simple.html")


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

            obs = LinkDataController.objects.filter(id=pk)
            entry = obs[0]

            w = EntryWrapper(entry=entry)
            if entry.bookmarked:
                new_entry = w.make_bookmarked(request)
            else:
                new_entry = w.make_not_bookmarked(request)

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


def remove_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Remove entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.filter(id=pk)
    if entry.exists():
        entry.delete()

        p.context["summary_text"] = "Remove ok"
    else:
        p.context["summary_text"] = "No source for ID: " + str(pk)

    return p.render("summary_present.html")


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


def entry_show_dislikes(request, pk):
    p = ViewPage(request)
    p.set_title("Show entry likes/dislikes")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    handler = UrlHandler.get_type(obj.link)

    if type(handler) == UrlHandler.youtube_video_handler:
        code = handler.get_video_code()
        h = ReturnDislike(code)
        up = h.get_thumbs_up()
        down = h.get_thumbs_down()
        view_count = h.get_view_count()
        rating = h.get_rating()
        p.context["summary_text"] = "Likes:{}\nDislikes:{}\nViews:{}\nRating:{}".format(
            up, down, view_count, rating
        )

    else:
        p.context["summary_text"] = "It is not a youtube link"

    return p.render("summary_present.html")


def entries_search_init(request):
    p = ViewPage(request)
    p.set_title("Search entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    user = request.user.username
    user_choices = UserSearchHistory.get_user_choices(request.user)
    if user_choices and len(user_choices) > 0:
        filter_form = OmniSearchForm(request=request, user_choices=user_choices)
    else:
        filter_form = InitSearchForm(request=request)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries".format(LinkDatabase.name))

    context = get_generic_search_init_context(request, filter_form, user_choices)

    p.context.update(context)

    return p.render("form_search_init.html")


def entries_omni_search_init(request):
    p = ViewPage(request)
    p.set_title("Search entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    user = request.user.username
    user_choices = UserSearchHistory.get_user_choices(request.user)
    if user_choices and len(user_choices) > 0:
        filter_form = OmniSearchForm(request=request, user_choices=user_choices)
    else:
        filter_form = InitSearchForm(request=request)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-omni-search".format(LinkDatabase.name))

    context = get_generic_search_init_context(request, filter_form, user_choices)
    p.context.update(context)

    return p.render("form_search_init.html")


def entries_bookmarked_init(request):
    p = ViewPage(request)
    p.set_title("Bookmarked entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    user = request.user.username
    user_choices = UserSearchHistory.get_user_choices(request.user)
    if user_choices and len(user_choices) > 0:
        filter_form = OmniSearchForm(request=request, user_choices=user_choices)
    else:
        filter_form = InitSearchForm(request=request)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-bookmarked".format(LinkDatabase.name))

    context = get_generic_search_init_context(request, filter_form, user_choices)
    p.context.update(context)

    return p.render("form_search_init.html")


def user_entries_bookmarked_init(request):
    p = ViewPage(request)
    p.set_title("Bookmarked entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    user = request.user.username
    user_choices = UserSearchHistory.get_user_choices(request.user)
    if user_choices and len(user_choices) > 0:
        filter_form = OmniSearchForm(request=request, user_choices=user_choices)
    else:
        filter_form = InitSearchForm(request=request)
    filter_form.method = "GET"
    filter_form.action_url = reverse(
        "{}:user-entries-bookmarked".format(LinkDatabase.name)
    )

    context = get_generic_search_init_context(request, filter_form, user_choices)
    p.context.update(context)

    return p.render("form_search_init.html")


def entries_recent_init(request):
    p = ViewPage(request)
    p.set_title("Search recent entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    user = request.user.username
    user_choices = UserSearchHistory.get_user_choices(request.user)
    if user_choices and len(user_choices) > 0:
        filter_form = OmniSearchForm(request=request, user_choices=user_choices)
    else:
        filter_form = InitSearchForm(request=request)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-recent".format(LinkDatabase.name))

    context = get_generic_search_init_context(request, filter_form, user_choices)
    p.context.update(context)

    return p.render("form_search_init.html")


def entries_archived_init(request):
    p = ViewPage(request)
    p.set_title("Search archive entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    user = request.user.username
    user_choices = UserSearchHistory.get_user_choices(request.user)
    if user_choices and len(user_choices) > 0:
        filter_form = OmniSearchForm(request=request, user_choices=user_choices)
    else:
        filter_form = InitSearchForm(request=request)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-archived".format(LinkDatabase.name))

    context = get_generic_search_init_context(request, filter_form, user_choices)
    p.context.update(context)

    return p.render("form_search_init.html")


def make_bookmarked_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=pk)

    new_entry = EntryWrapper(entry=entry).make_bookmarked(request)

    if new_entry:
        if Configuration.get_object().config_entry.link_save:
            BackgroundJobController.link_save(entry.link)

    return HttpResponseRedirect(new_entry.get_absolute_url())


def make_not_bookmarked_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Not bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=pk)
    new_entry = EntryWrapper(entry=entry).make_not_bookmarked(request)

    return HttpResponseRedirect(new_entry.get_absolute_url())


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

    if Configuration.get_object().config_entry.link_save:
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

    # JsonResponse
    return JsonResponse(json_obj)


def entries_json(request):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    found_view = False

    query_type = "standard"
    if "query_type" in request.GET:
        query_type = request.GET["query_type"]

    check_views = [
        EntriesSearchListView,
        EntriesRecentListView,
        EntriesBookmarkedListView,
        EntriesNotTaggedView,
        EntriesArchiveListView,
        EntriesOmniListView,
    ]

    view_to_use = None

    for view_class in check_views:
        view = view_class()
        view.request = request
        if query_type == view.get_query_type():
            view_to_use = view

    page_num = get_page_num(request.GET)

    if view_to_use:
        links = view_to_use.get_queryset()
        p = Paginator(links, view.get_paginate_by(links))
        page_obj = p.get_page(page_num)

        objects = links[page_obj.start_index() - 1 : page_obj.end_index()]

        exporter = InstanceExporter()
        json_obj = exporter.export_links(objects)

        # JsonResponse
        return JsonResponse(json_obj)


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
