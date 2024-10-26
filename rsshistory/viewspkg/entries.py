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

    return p.render("entry_list.html")


def entries(request):
    return entries_generic(request, reverse("{}:entries-json".format(LinkDatabase.name)))


def entries_recent(request):
    return entries_generic(request, reverse("{}:entries-json-recent".format(LinkDatabase.name)))


def entries_bookmarked(request):
    return entries_generic(request, reverse("{}:entries-json-bookmarked".format(LinkDatabase.name)))


def entries_user_bookmarked(request):
    return entries_generic(request, reverse("{}:entries-json-user-bookmarked".format(LinkDatabase.name)))


def entries_archived(request):
    return entries_generic(request, reverse("{}:entries-json-archived".format(LinkDatabase.name)))


def entries_untagged(request):
    return entries_generic(request, reverse("{}:entries-json-untagged".format(LinkDatabase.name)))

    return p.render("entries.html")


class EntriesSearchListView(object):

    def get_queryset(self):
        """
        API: Returns queryset
        """
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
            config = ConfigurationEntry.get().config_entry
            return config.links_per_page
        else:
            uc = UserConfig.get(self.request.user)
            return uc.links_per_page

    def get_order_by(self):
        return get_order_by(self.request.GET)

    def get_filter(self):
        self.on_search()
        print("EntriesSearchListView:get_filter")

        query_filter = EntryFilter(self.request.GET, self.request.user)
        thefilter = query_filter
        print("EntriesSearchListView:get_filter done")
        return thefilter

    def get_filtered_objects(self):
        print("EntriesSearchListView:get_filtered_objects")
        return self.query_filter.get_filtered_objects()

    def on_search(self):
        if self.request.user.is_authenticated:
            search_term = get_search_term(self.request.GET)
            if search_term:
                UserSearchHistory.add(self.request.user, search_term)



class EntriesOmniListView(EntriesSearchListView):
    def get_filter(self):
        self.on_search()

        if ("archive" in self.request.GET and self.request.GET["archive"] == "on"):
            query_set = self.get_initial_query_set(archive=True)
        else:
            query_set = self.get_initial_query_set(archive=False)

        query_filter = OmniSearchFilter(self.request.GET, init_objects = query_set)

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

    def get_filtered_objects(self):
        return self.query_filter.get_filtered_objects()

    def get_initial_query_set(self, archive=False):
        """
        TODO rewrite. Filter should return only query sets. pure. without pagination
        """
        if archive:
            return ArchiveLinkDataController.objects.all()
        else:
            return LinkDataController.objects.all()


class EntriesRecentListView(EntriesOmniListView):
    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        return query_set.filter(date_published__range=self.get_default_range())

    def get_order_by(self):
        return ["-date_published"]

    def get_default_range(self):
        config = ConfigurationEntry.get()
        return DateUtils.get_days_range(config.whats_new_days)


class EntriesNotTaggedView(EntriesOmniListView):

    def get_order_by(self):
        return ["-date_published"]

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        tags_is_null = Q(tags__isnull=True)
        bookmarked = Q(bookmarked=True)
        permanent = Q(permanent=True)
        return query_set.filter(tags_is_null & (bookmarked | permanent))


class EntriesBookmarkedListView(EntriesOmniListView):

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        return query_set.filter(bookmarked=1)


class UserEntriesBookmarkedListView(EntriesOmniListView):

    def get_initial_query_set(self, archive=False):
        query_set = super().get_initial_query_set(archive)
        user = self.request.user
        return query_set.filter(bookmarks__user__id=user.id)


class EntriesArchiveListView(EntriesOmniListView):

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET, self.request.user, use_archive=True)
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
    template_name = str(ViewPage.get_full_template("entry_detail__dynamic.html"))

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

    template_name = str(ViewPage.get_full_template("entry_detail.html"))

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


def get_entry_menu(request, pk):
    p = ViewPage(request)
    p.set_title("Get entry menu")

    uc = UserConfig.get(request.user)
    if not uc.can_add():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    entries = LinkDataController.objects.filter(id = pk)
    if entries.exists():
        entry = entries[0]
        p.context["object"] = entry
        p.context["user"] = request.user
        p.context["object_controller"] = EntryPreviewBuilder.get(
            entry, request.user,
        )

    return p.render("entry_detail__buttons.html")


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


def entry_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.filter(id=pk)
    status_code = 200

    data = {
            "status" : False,
            "message" : "",
    }

    if entry.exists():
        entry.delete()

        data["message"] = "Remove ok"
        data["status"] = True
    else:
        data["message"] = "No source for ID: " + str(pk)
        data["status"] = False

    return JsonResponse(data)


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
        if Configuration.get_object().config_entry.link_save:
            BackgroundJobController.link_save(entry.link)

        json_obj["status"] = True
        json_obj["message"] = "Bookmarked"

    # JsonResponse
    return JsonResponse(json_obj)


def entry_unbookmark(request, pk):
    p = ViewPage(request)
    p.set_title("Not bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=pk)
    new_entry = EntryWrapper(entry=entry).make_not_bookmarked(request)

    json_obj = {
            "status" : True,
            "message" : "Unbookmarked",
    }

    # JsonResponse
    return JsonResponse(json_obj)


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


def entry_to_json(user_config, entry):
    json_entry = {}
    json_entry["id"] = entry.id
    json_entry["title"] = entry.title
    json_entry["title_safe"] = entry.get_title_safe()
    json_entry["description"] = entry.description
    json_entry["description_safe"] = entry.get_description_safe()
    json_entry["link"] = entry.link
    json_entry["link_absolute"] = entry.get_absolute_url()
    json_entry["is_valid"] = entry.is_valid()
    json_entry["date_published"] = entry.date_published
    json_entry["date_dead_since"] = entry.date_dead_since
    json_entry["date_update_last"] = entry.date_update_last
    json_entry["bookmarked"] = entry.bookmarked
    json_entry["permanent"] = entry.permanent
    json_entry["artist"] = entry.artist
    json_entry["album"] = entry.album
    json_entry["page_rating_contents"] = entry.page_rating_contents
    json_entry["page_rating_votes"] = entry.page_rating_votes

    json_entry["source__title"] = ""
    json_entry["source__url"] = ""

    if hasattr(entry, "source"):
        if entry.source:
            json_entry["source__title"] = entry.source.title
            json_entry["source__url"] = entry.source.url

    if user_config.show_icons:
        if user_config.thumbnails_as_icons:
            json_entry["thumbnail"] = entry.get_thumbnail()
        else:
            json_entry["thumbnail"] = entry.get_favicon()

    return json_entry


def handle_json_view(request, view_to_use):
    page_num = get_page_num(request.GET)

    json_obj = {}
    json_obj["entries"] = []
    json_obj["count"] = 0
    json_obj["page"] = page_num
    json_obj["num_pages"] = 0

    uc = UserConfig.get(request.user)

    if view_to_use:
        entries = view_to_use.get_queryset()
        p = Paginator(entries, view_to_use.get_paginate_by(entries))
        page_obj = p.get_page(page_num)

        json_obj["count"] = p.count
        json_obj["num_pages"] = p.num_pages

        start = page_obj.start_index()
        if start > 0:
            start -= 1

        limited_entries = entries[start : page_obj.end_index()]

        for entry in limited_entries:
            entry_json = entry_to_json(uc, entry)

            json_obj["entries"].append(entry_json)

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

    view = EntriesSearchListView()
    view.request = request

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

    view = EntriesRecentListView()
    view.request = request

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

    view = EntriesBookmarkedListView()
    view.request = request

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

    view = UserEntriesBookmarkedListView()
    view.request = request

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

    view = EntriesArchiveListView()
    view.request = request

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

    view = EntriesNotTaggedView()
    view.request = request

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
