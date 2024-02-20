from datetime import datetime

from django.views import generic
from django.urls import reverse
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlencode

from ..apps import LinkDatabase
from ..models import (
    BaseLinkDataController,
    BackgroundJob,
    ConfigurationEntry,
    Domains,
    UserEntryVisitHistory,
    UserSearchHistory,
    UserEntryTransitionHistory,
)
from ..controllers import (
    LinkDataController,
    LinkDataWrapper,
    LinkDataBuilder,
    ArchiveLinkDataController,
    SourceDataController,
    BackgroundJobController,
    SearchEngines,
)
from ..forms import (
    EntryForm,
    EntryChoiceForm,
    ConfigForm,
    EntryBookmarksChoiceForm,
    EntryRecentChoiceForm,
    OmniSearchForm,
    OmniSearchWithArchiveForm,
)
from ..queryfilters import EntryFilter
from ..views import ViewPage
from ..configuration import Configuration
from ..webtools import Url, BasePage
from ..services.waybackmachine import WaybackMachine
from ..dateutils import DateUtils
from ..serializers.instanceimporter import InstanceExporter
from .plugins.entrypreviewbuilder import EntryPreviewBuilder


def get_search_term_request(request):
    search_term = ""
    if "title" in request.GET and request.GET["title"] != "":
        search_term = request.GET["title"]
    elif "tag" in request.GET and request.GET["tag"] != "":
        search_term = request.GET["tag"]
    elif "search_history" in request.GET and request.GET["search_history"] != "":
        search_term = request.GET["search_history"]
    elif "search" in request.GET and request.GET["search"] != "":
        search_term = request.GET["search"]

    return search_term


class EntriesSearchListView(generic.ListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("linkdatacontroller_list.html"))

    def get(self, *args, **kwargs):
        print("EntriesSearchListView:get")

        self.time_start = datetime.now()

        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        print("EntriesSearchListView:get constructor of list view")
        view = super(EntriesSearchListView, self).get(*args, **kwargs)
        print("EntriesSearchListView:get done")
        return view

    def get_filter(self):
        print("EntriesSearchListView:get_filter")
        query_filter = EntryFilter(self.request.GET)
        query_filter.get_sources()
        thefilter = query_filter
        print("EntriesSearchListView:get_filter done")
        return thefilter

    def get_queryset(self):
        config = Configuration.get_object().config_entry

        print("EntriesSearchListView:get_queryset")
        self.query_filter = self.get_filter()
        objects = self.get_filtered_objects().order_by(*config.get_entries_order_by())
        print("EntriesSearchListView:get_queryset done {}".format(objects.query))
        return objects

    def get_context_data(self, **kwargs):
        print("EntriesSearchListView:get_context_data")
        # Call the base implementation first to get the context
        context = super(EntriesSearchListView, self).get_context_data(**kwargs)

        context = ViewPage.init_context(self.request, context)
        # Create any data and add it to the context
        self.init_display_type(context)

        context["page_title"] += self.get_title()

        queue_size = BackgroundJobController.get_number_of_jobs(
            BackgroundJob.JOB_PROCESS_SOURCE
        )
        context["rss_are_fetched"] = queue_size > 0
        context["rss_queue_size"] = queue_size

        context["query_filter"] = self.query_filter
        context["reset_link"] = self.get_reset_link()
        context["more_results_link"] = self.get_more_results_link()
        context["has_more_results"] = self.has_more_results()
        context["query_type"] = self.get_query_type()

        self.filter_form = self.get_form()
        context["filter_form"] = self.filter_form

        search_term = get_search_term_request(self.request)

        context["search_engines"] = SearchEngines(search_term)

        print(
            "EntriesSearchListView:get_context_data done. View time delta:{}".format(
                datetime.now() - self.time_start
            )
        )

        return context

    def get_filtered_objects(self):
        print("EntriesSearchListView:get_filtered_objects")
        return self.query_filter.get_filtered_objects()

    def get_reset_link(self):
        return reverse("{}:entries-search-init".format(LinkDatabase.name))

    def has_more_results(self):
        return True

    def get_more_results_link(self):
        return (
            reverse("{}:entries-omni-search".format(LinkDatabase.name))
            + "?"
            + self.query_filter.get_filter_string()
        )

    def get_form_action_link(self):
        return reverse("{}:entries".format(LinkDatabase.name))

    def get_form_instance(self):
        return EntryChoiceForm(self.request.GET)

    def get_form(self):
        filter_form = self.get_form_instance()
        filter_form.create(self.query_filter.sources)

        filter_form.method = "GET"
        filter_form.action_url = self.get_form_action_link()

        return filter_form

    def get_title(self):
        return " - Links"

    def get_query_type(self):
        return "standard"

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

    def get_default_range(self):
        config = Configuration.get_object().config_entry
        return DateUtils.get_days_range(config.whats_new_days)


class EntriesRecentListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.set_time_limit(self.get_default_range())
        query_filter.get_sources()
        return query_filter

    def get_queryset(self):
        print("EntriesSearchListView:get_queryset")
        self.query_filter = self.get_filter()
        objects = self.get_filtered_objects()
        print("EntriesSearchListView:get_queryset done {}".format(objects.query))
        return objects

    def get_reset_link(self):
        return reverse("{}:entries-recent-init".format(LinkDatabase.name))

    def get_form_action_link(self):
        return reverse("{}:entries-recent".format(LinkDatabase.name))

    def get_form_instance(self):
        form = EntryRecentChoiceForm(self.request.GET, request=self.request)
        return form

    def get_title(self):
        return " - Recent"

    def get_query_type(self):
        return "recent"


class EntriesNotTaggedView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.get_sources()
        query_filter.set_additional_condition(
            Q(tags__tag__isnull=True, bookmarked=True)
        )
        return query_filter

    def has_more_results(self):
        return False

    def get_reset_link(self):
        return reverse("{}:entries-untagged".format(LinkDatabase.name))

    def get_form_action_link(self):
        return reverse("{}:entries-recent".format(LinkDatabase.name))

    def get_form_instance(self):
        return EntryChoiceForm(self.request.GET)

    def get_title(self):
        return " - UnTagged"

    def get_query_type(self):
        return "not-tagged"


class EntriesBookmarkedListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.get_sources()
        query_filter.set_additional_condition(Q(bookmarked=True))
        return query_filter

    def has_more_results(self):
        return False

    def get_reset_link(self):
        return reverse("{}:entries-bookmarked-init".format(LinkDatabase.name))

    def get_form_action_link(self):
        return reverse("{}:entries-bookmarked".format(LinkDatabase.name))

    def get_form_instance(self):
        return EntryBookmarksChoiceForm(self.request.GET)

    def get_title(self):
        return " - Bookmarked"

    def get_query_type(self):
        return "bookmarked"


class EntriesArchiveListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100
    template_name = str(ViewPage.get_full_template("linkdatacontroller_list.html"))

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.get_sources()
        query_filter.set_archive_source(True)
        return query_filter

    def has_more_results(self):
        return False

    def get_reset_link(self):
        return reverse("{}:entries-archived-init".format(LinkDatabase.name))

    def get_form_action_link(self):
        return reverse("{}:entries-archived".format(LinkDatabase.name))

    def get_form_instance(self):
        return EntryChoiceForm(self.request.GET)

    def get_title(self):
        return " - Archived"

    def get_query_type(self):
        return "archived"


class EntriesOmniListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        from ..queryfilters import OmniSearchFilter
        from ..models import UserSearchHistory

        username = self.request.user.username

        if self.request.user.is_authenticated:
            search_term = get_search_term_request(self.request)
            if search_term:
                UserSearchHistory.add(self.request.user, search_term)

        query_filter = OmniSearchFilter(self.request.GET)

        translate = BaseLinkDataController.get_query_names()
        query_filter.set_translatable(translate)

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

        query_filter.calculate_combined_query()

        return query_filter

    def get_filtered_objects(self):
        fields = self.query_filter.get_fields()

        if ("archive" in self.request.GET and self.request.GET["archive"] == "on") or (
            "archive" in fields and fields["archive"] == "1"
        ):
            self.query_filter.set_query_set(ArchiveLinkDataController.objects.all())
        else:
            self.query_filter.set_query_set(LinkDataController.objects.all())

        return self.query_filter.get_filtered_objects()

    def get_reset_link(self):
        return reverse("{}:entries-omni-search-init".format(LinkDatabase.name))

    def get_form_action_link(self):
        return reverse("{}:entries-omni-search".format(LinkDatabase.name))

    def has_more_results(self):
        if "archive" in self.request.GET:
            return False
        else:
            return True

    def get_more_results_link(self):
        if "search" in self.request.GET:
            return reverse(
                "{}:entries-omni-search".format(LinkDatabase.name)
            ) + "?archive=on&search={}".format(self.request.GET["search"])
        else:
            return (
                reverse("{}:entries-omni-search".format(LinkDatabase.name))
                + "?archive=on"
            )

    def get_form_instance(self):
        config = Configuration.get_object().config_entry

        user = self.request.user
        user_choices = UserSearchHistory.get_user_choices(user)

        if config.days_to_move_to_archive == 0:
            f = OmniSearchForm(
                self.request.GET, user_choices=user_choices, request=self.request
            )
            return f
        else:
            return OmniSearchWithArchiveForm(
                self.request.GET, user_choices=user_choices
            )

    def get_form(self):
        filter_form = self.get_form_instance()
        filter_form.method = "GET"
        filter_form.action_url = self.get_form_action_link()

        return filter_form

    def get_title(self):
        return " - Links"

    def get_query_type(self):
        return "omni"


class EntryDetailView(generic.DetailView):
    model = LinkDataController

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(EntryDetailView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

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

        config = Configuration.get_object().config_entry
        if config.track_user_actions and config.track_user_navigation:
            username = self.request.user.username
            context["transitions"] = UserEntryTransitionHistory.get_related_list(
                self.request.user, self.object
            )

        m = WaybackMachine()
        context["archive_org_date"] = m.get_formatted_date(DateUtils.get_date_today())
        context["search_engines"] = SearchEngines(
            self.object.get_search_term(), self.object.link
        )

        return context

    def set_visited(self):
        UserEntryVisitHistory.visited(self.object, self.request.user)


class EntryArchivedDetailView(generic.DetailView):
    model = ArchiveLinkDataController

    template_name = str(ViewPage.get_full_template("linkdatacontroller_detail.html"))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(EntryArchivedDetailView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

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


def add_entry(request):
    from ..controllers import LinkDataController

    p = ViewPage(request)
    p.set_title("Add entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = EntryForm(request.POST)

        # check whether it's valid:
        valid = form.is_valid()
        link = request.POST.get("link", "")

        ob = LinkDataWrapper(link=link).get()
        if ob:
            return HttpResponseRedirect(ob.get_absolute_url())

        if valid:
            data = form.get_information()

            b = LinkDataBuilder()
            b.link_data = data
            b.source_is_auto = False
            entry = b.add_from_props_internal()

            if not entry:
                p.context["summary_text"] = "Could not save link"
                return p.render("summary_present.html")

            p.context["form"] = form

            if entry:
                p.context["entry"] = entry

            config = Configuration.get_object().config_entry

            if config.link_save:
                BackgroundJobController.link_save(data["link"])

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
        author = request.user.username
        initial = {"user": author}
        if "link" in request.GET:
            initial["link"] = request.GET["link"]

        form = EntryForm(initial=initial)
        form.method = "POST"
        form.action_url = reverse("{}:entry-add".format(LinkDatabase.name))
        p.context["form"] = form

        p.context["form_title"] = "Add new entry"

        form_text = "<pre>"
        form_text += "Required fields:\n"
        form_text += " - Link [required]\n"
        form_text += "\n"
        form_text += "For YouTube links:\n"
        form_text += " - Title, description, Date published, source, language is set automatically\n"
        form_text += " - manual setting of language overrides the default (en)\n"
        form_text += "\n"
        form_text += "For standard links:\n"
        form_text += " - Title, description, source, language is set automatically, if not specified\n"
        form_text += " - Always specify date published [required]\n"
        form_text += " - Better specify language\n"
        form_text += " - In case of errors, specify title, and description\n"
        form_text += "</pre>"

        p.context["form_description_post"] = form_text

    return p.render("form_basic.html")


def add_simple_entry(request):
    from ..forms import ExportDailyDataForm, LinkInputForm

    p = ViewPage(request)
    p.set_title("Add entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = LinkInputForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data["link"]
            link = LinkDataController.get_cleaned_link(link)

            if not Url.is_web_link(link):
                p.context[
                    "summary_text"
                ] = "Only http links are allowed. Link:{}".format(link)
                return p.render("summary_present.html")

            data = LinkDataController.get_full_information({"link": link})
            if data:
                notes = []
                warnings = []
                errors = []

                obs = LinkDataController.objects.filter(link=data["link"])
                if obs.exists():
                    ob = obs[0]
                    return HttpResponseRedirect(ob.get_absolute_url())

                data["user"] = request.user.username
                data["bookmarked"] = True

                if "description" in data:
                    data["description"] = LinkDataController.get_description_safe(
                        data["description"]
                    )

                form = EntryForm(initial=data)
                form.method = "POST"
                form.action_url = reverse("{}:entry-add".format(LinkDatabase.name))
                p.context["form"] = form

                page = BasePage(data["link"])
                domain = page.get_domain()

                if data["link"].find("http://") >= 0:
                    warnings.append("Link is http. Https is more secure protocol")
                if (
                    data["link"].find("http://") == -1
                    and data["link"].find("https://") == -1
                ):
                    errors.append("Missing protocol. Could be http:// or https://")
                if domain.lower() != domain:
                    warnings.append("Link domain is not lowercase. Is that OK?")

                p.context["notes"] = notes
                p.context["warnings"] = warnings
                p.context["errors"] = errors

                return p.render("form_add_entry.html")

            p.context["summary_text"] = "Could not obtain details from link {}".format(
                link
            )
            return p.render("summary_present.html")
    else:
        form = LinkInputForm()
        form.method = "POST"

        p.context["form"] = form
        p.context["form_description_post"] = "Internet is dangerous, so carefully select which links you add"

        return p.render("form_basic.html")


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
        BackgroundJobController.entry_update_data(entry, True)
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
        BackgroundJobController.entry_reset_data(entry, True)
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
    if ob.user is None or ob.user == "":
        ob.user = str(request.user.username)
        ob.save()

    if ob.description:
        ob.description = LinkDataController.get_description_safe(ob.description)
        ob.save()

    if request.method == "POST":
        form = EntryForm(request.POST, instance=ob)
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
        form = EntryForm(instance=ob)
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


def entry_dead(request, pk):
    p = ViewPage(request)
    p.set_title("Mark entry as dead")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    obj.make_dead(True)

    summary_text = "Link changed to state: " + str(obj.dead)

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def entry_not_dead(request, pk):
    p = ViewPage(request)
    p.set_title("Marking entry as not dead")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    obj.make_dead(False)

    summary_text = "Link changed to state: " + str(obj.dead)

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def entries_search_init(request):
    p = ViewPage(request)
    p.set_title("Search entries")

    filter_form = EntryChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries".format(LinkDatabase.name))

    p.context["form"] = filter_form

    search_term = get_search_term_request(request)
    p.context["search_term"] = search_term
    p.context["search_engines"] = SearchEngines(search_term)

    return p.render("form_search.html")


def entries_omni_search_init(request):
    p = ViewPage(request)
    p.set_title("Search entries")

    user = request.user.username
    user_choices = UserSearchHistory.get_user_choices(request.user)

    filter_form = OmniSearchForm(
        request.GET, user_choices=user_choices, request=request
    )
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-omni-search".format(LinkDatabase.name))

    p.context["form"] = filter_form

    search_term = get_search_term_request(request)
    p.context["search_term"] = search_term
    p.context["search_engines"] = SearchEngines(search_term)

    return p.render("form_search_omni.html")


def entries_bookmarked_init(request):
    p = ViewPage(request)
    p.set_title("Bookmarked entries")

    filter_form = EntryBookmarksChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-bookmarked".format(LinkDatabase.name))

    p.context["form"] = filter_form

    search_term = get_search_term_request(request)
    p.context["search_term"] = search_term
    p.context["search_engines"] = SearchEngines(search_term)

    return p.render("form_search.html")


def entries_recent_init(request):
    p = ViewPage(request)
    p.set_title("Search recent entries")

    filter_form = EntryRecentChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-recent".format(LinkDatabase.name))

    p.context["form"] = filter_form

    search_term = get_search_term_request(request)
    p.context["search_term"] = search_term
    p.context["search_engines"] = SearchEngines(search_term)

    return p.render("form_search.html")


def entries_archived_init(request):
    p = ViewPage(request)
    p.set_title("Search archive entries")

    filter_form = EntryChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-archived".format(LinkDatabase.name))

    p.context["form"] = filter_form

    return p.render("form_search.html")


def make_bookmarked_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Bookmark entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=pk)

    new_entry = LinkDataWrapper.make_bookmarked(request, entry)

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
    new_entry = LinkDataWrapper.make_not_bookmarked(request, entry)

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

    return p.render("summary_present.html")


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

    return p.render("summary_present.html")


def entry_json(request, pk):
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
    found_view = False

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

    page_limit = "standard"
    if "page_limit" in request.GET:
        page_limit = request.GET["page_limit"]

        for view_class in check_views:
            view = view_class()
            view.request = request
            if query_type == view.get_query_type():
                query_filter = view.get_filter()
                if page_limit != "no-limit":
                    query_filter.use_page_limit = True
                found_view = True
                break

    if not found_view:
        view = check_views[0]()
        view.request = request
        query_filter = view.get_filter()
        query_filter.use_page_limit = True

    links = query_filter.get_filtered_objects()

    exporter = InstanceExporter()
    json_obj = exporter.export_links(links)

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

    new_entry = LinkDataWrapper.make_bookmarked(request, entry)

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
    new_entry = LinkDataWrapper.make_not_bookmarked(request, entry)

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
        form = EntryArchiveForm(request.POST, instance=ob)
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
        form = EntryArchiveForm(instance=ob)
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
