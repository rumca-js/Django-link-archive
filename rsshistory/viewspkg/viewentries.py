from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.db.models import Q
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..models import (
    LinkTagsDataModel,
    BackgroundJob,
    ConfigurationEntry,
    ArchiveLinkDataModel,
    Domains,
)
from ..controllers import (
    LinkDataController,
    LinkDataHyperController,
    ArchiveLinkDataController,
    SourceDataController,
    BackgroundJobController,
)
from ..forms import (
    EntryForm,
    EntryChoiceForm,
    ConfigForm,
    BasicEntryChoiceForm,
    EntryBookmarksChoiceForm,
    OmniSearchForm,
)
from ..queryfilters import EntryFilter
from ..views import ContextData
from ..configuration import Configuration


class EntriesSearchListView(generic.ListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100
    template_name = str(ContextData.get_full_template("linkdatacontroller_list.html"))

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.get_sources()
        query_filter.set_time_constrained(False)
        return query_filter

    def get_queryset(self):
        self.query_filter = self.get_filter()
        return self.query_filter.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(EntriesSearchListView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)
        # Create any data and add it to the context

        context["page_title"] += self.get_title()

        queue_size = BackgroundJobController.get_number_of_jobs(
            BackgroundJob.JOB_PROCESS_SOURCE
        )
        context["rss_are_fetched"] = queue_size > 0
        context["rss_queue_size"] = queue_size

        context["query_filter"] = self.query_filter
        context["reset_link"] = self.get_reset_link()
        context["query_type"] = self.get_query_type()

        self.filter_form = self.get_form()
        context["filter_form"] = self.filter_form

        if "title" in self.request.GET:
            context["search_term"] = self.request.GET["title"]
        elif "tag" in self.request.GET:
            context["search_term"] = self.request.GET["tag"]
        elif "search" in self.request.GET:
            context["search_term"] = self.request.GET["search"]

        return context

    def get_reset_link(self):
        return reverse("{}:entries-search-init".format(ContextData.app_name))

    def get_form_action_link(self):
        return reverse("{}:entries".format(ContextData.app_name))

    def get_form_instance(self):
        return EntryChoiceForm(self.request.GET)

    def get_form(self):
        filter_form = self.get_form_instance()
        filter_form.create(self.query_filter.sources)

        filter_form.method = "GET"
        filter_form.action_url = self.get_form_action_link()

        return filter_form

    def get_title(self):
        return " - entries"

    def get_query_type(self):
        return "standard"


class EntriesRecentListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.get_sources()
        return query_filter

    def get_reset_link(self):
        return reverse("{}:entries-recent-init".format(ContextData.app_name))

    def get_form_action_link(self):
        return reverse("{}:entries-recent".format(ContextData.app_name))

    def get_form_instance(self):
        return BasicEntryChoiceForm(self.request.GET)

    def get_title(self):
        return " - entries"

    def get_query_type(self):
        return "recent"


class EntriesNotTaggedView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.set_time_constrained(False)
        query_filter.get_sources()
        query_filter.set_additional_condition(Q(tags__tag__isnull=True, bookmarked=True))
        return query_filter

    def get_reset_link(self):
        return reverse("{}:entries-untagged".format(ContextData.app_name))

    def get_form_action_link(self):
        return reverse("{}:entries-recent".format(ContextData.app_name))

    def get_form_instance(self):
        return EntryChoiceForm(self.request.GET)

    def get_title(self):
        return " - not tagged"

    def get_query_type(self):
        return "not-tagged"


class EntriesBookmarkedListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.set_time_constrained(False)
        query_filter.get_sources()
        query_filter.set_additional_condition(Q(bookmarked=True))
        return query_filter

    def get_reset_link(self):
        return reverse("{}:entries-bookmarked-init".format(ContextData.app_name))

    def get_form_action_link(self):
        return reverse("{}:entries-bookmarked".format(ContextData.app_name))

    def get_form_instance(self):
        return EntryBookmarksChoiceForm(self.request.GET)

    def get_title(self):
        return " - bookmarked"

    def get_query_type(self):
        return "bookmarked"


class EntriesArchiveListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100
    template_name = str(ContextData.get_full_template("linkdatacontroller_list.html"))

    def get_filter(self):
        query_filter = EntryFilter(self.request.GET)
        query_filter.get_sources()
        query_filter.set_archive_source(True)
        return query_filter

    def get_reset_link(self):
        return reverse("{}:entries-archived-init".format(ContextData.app_name))

    def get_form_action_link(self):
        return reverse("{}:entries-archived".format(ContextData.app_name))

    def get_form_instance(self):
        return EntryChoiceForm(self.request.GET)

    def get_title(self):
        return " - archived"

    def get_query_type(self):
        return "archived"


class EntriesOmniListView(EntriesSearchListView):
    model = LinkDataController
    context_object_name = "content_list"
    paginate_by = 100

    def get_filter(self):
        from ..queryfilters import OmniSearchFilter
        query_filter = OmniSearchFilter(self.request.GET)
        query_filter.set_query_set(LinkDataController.objects.all())
        return query_filter

    def get_reset_link(self):
        return reverse("{}:entries-omni-search-init".format(ContextData.app_name))

    def get_form_action_link(self):
        return reverse("{}:entries-omni-search".format(ContextData.app_name))

    def get_form_instance(self):
        return OmniSearchForm(self.request.GET)

    def get_form(self):
        filter_form = self.get_form_instance()
        filter_form.method = "GET"
        filter_form.action_url = self.get_form_action_link()

        return filter_form

    def get_title(self):
        return " - entries"

    def get_query_type(self):
        return "omni"


class EntryDetailView(generic.DetailView):
    model = LinkDataController

    def get_context_data(self, **kwargs):
        from ..pluginentries.entrycontrollerbuilder import EntryControllerBuilder

        # Call the base implementation first to get the context
        context = super(EntryDetailView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        if self.object.language == None:
            self.object.update_language()

        context["page_title"] = self.object.title
        context["object_controller"] = EntryControllerBuilder.get(self.object)

        from ..services.waybackmachine import WaybackMachine
        from ..dateutils import DateUtils

        m = WaybackMachine()
        context["archive_org_date"] = m.get_formatted_date(DateUtils.get_date_today())

        return context


class EntryArchivedDetailView(generic.DetailView):
    model = ArchiveLinkDataController

    template_name = str(ContextData.get_full_template("linkdatacontroller_detail.html"))

    def get_context_data(self, **kwargs):
        from ..pluginentries.entrycontrollerbuilder import EntryControllerBuilder

        # Call the base implementation first to get the context
        context = super(EntryArchivedDetailView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        if self.object.language == None:
            self.object.update_language()

        context["page_title"] = self.object.title
        context["object_controller"] = EntryControllerBuilder.get(self.object)

        from ..services.waybackmachine import WaybackMachine
        from ..dateutils import DateUtils

        m = WaybackMachine()
        context["archive_org_date"] = m.get_formatted_date(DateUtils.get_date_today())

        return context


def add_entry(request):
    from ..controllers import LinkDataController

    context = ContextData.get_context(request)
    context["page_title"] += " - Add entry"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = EntryForm(request.POST)

        # check whether it's valid:
        valid = form.is_valid()
        link = request.POST.get("link", "")

        ob = LinkDataController.objects.filter(link=link)
        if ob.exists():
            context["form"] = form
            context["entry"] = ob[0]

            return ContextData.render(request, "entry_edit_exists.html", context)

        if valid:
            data = form.get_information()
            if not LinkDataHyperController.add_new_link(data):
                context["summary_text"] = "Could not save link"
                return ContextData.render(request, "summary_present.html", context)

            context["form"] = form

            ob = LinkDataController.objects.filter(link=data["link"])
            if ob.exists():
                context["entry"] = ob[0]

            if ConfigurationEntry.get().store_domain_info:
                Domains.add(data["link"])

            if ConfigurationEntry.get().link_archive:
                BackgroundJobController.link_archive(data["link"])

            return ContextData.render(request, "entry_added.html", context)

        context["summary_text"] = "Form is invalid"
        return ContextData.render(request, "summary_present.html", context)

    else:
        author = request.user.username
        initial = {"user": author}
        if "link" in request.GET:
            initial["link"] = request.GET["link"]

        form = EntryForm(initial=initial)
        form.method = "POST"
        form.action_url = reverse("{}:entry-add".format(ContextData.app_name))
        context["form"] = form

        context["form_title"] = "Add new entry"

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

        context["form_description_post"] = form_text

    return ContextData.render(request, "form_basic.html", context)


def add_simple_entry(request):
    from ..forms import ExportDailyDataForm, LinkInputForm
    from ..controllers import LinkDataController

    context = ContextData.get_context(request)
    context["page_title"] += " - Add simple entry"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = LinkInputForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data["link"]

            ob = LinkDataController.objects.filter(link=link)
            if ob.exists():
                context["form"] = form
                context["entry"] = ob[0]

                return ContextData.render(request, "entry_edit_exists.html", context)

            data = LinkDataController.get_full_information({"link": link})
            data["user"] = request.user.username

            form = EntryForm(initial=data)
            form.method = "POST"
            form.action_url = reverse("{}:entry-add".format(ContextData.app_name))
            context["form"] = form

            return ContextData.render(request, "form_basic.html", context)
    else:
        form = LinkInputForm()
        form.method = "POST"

        context["form"] = form

        return ContextData.render(request, "form_basic.html", context)


def edit_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - edit entry"

    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    obs = LinkDataController.objects.filter(id=pk)
    if not obs.exists():
        context["summary_text"] = "Such entry does not exist"
        return ContextData.render(request, "summary_present.html", context)

    ob = obs[0]
    if ob.user is None or ob.user == "":
        ob.user = str(request.user.username)
        ob.save()

    if request.method == "POST":
        form = EntryForm(request.POST, instance=ob)
        context["form"] = form

        if form.is_valid():
            form.save()

            context["entry"] = ob
            return ContextData.render(request, "entry_edit_ok.html", context)

        context["summary_text"] = "Could not edit entry"

        return ContextData.render(request, "summary_present.html", context)
    else:
        form = EntryForm(instance=ob)
        form.method = "POST"
        form.action_url = reverse(
            "{}:entry-edit".format(ContextData.app_name), args=[pk]
        )
        context["form"] = form
        return ContextData.render(request, "form_basic.html", context)


def remove_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove entry"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    entry = LinkDataController.objects.filter(id=pk)
    if entry.exists():
        entry.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return ContextData.render(request, "summary_present.html", context)


def hide_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - hide entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    objs = LinkDataController.objects.filter(id=pk)
    obj = objs[0]

    fav = obj.dead
    obj.dead = not obj.dead
    obj.save()

    summary_text = "Link changed to state: " + str(obj.dead)

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


def entries_search_init(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - search filter"

    filter_form = EntryChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries".format(ContextData.app_name))

    context["form"] = filter_form

    return ContextData.render(request, "form_search.html", context)


def entries_omni_search_init(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - search filter"

    filter_form = OmniSearchForm()
    filter_form.method = "GET"
    filter_form.action_url = reverse(
        "{}:entries-omni-search".format(ContextData.app_name)
    )

    context["form"] = filter_form

    if "search" in request.GET:
        context["search_term"] = self.request.GET["search"]

    return ContextData.render(request, "form_search_omni.html", context)


def entries_bookmarked_init(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - bookmarked filter"

    filter_form = EntryBookmarksChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse(
        "{}:entries-bookmarked".format(ContextData.app_name)
    )

    context["form"] = filter_form

    return ContextData.render(request, "form_search.html", context)


def entries_recent_init(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - recent filter"

    filter_form = BasicEntryChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-recent".format(ContextData.app_name))

    context["form"] = filter_form

    return ContextData.render(request, "form_search.html", context)


def entries_archived_init(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - init filter"

    filter_form = EntryChoiceForm()
    filter_form.create(SourceDataController.objects.all())
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:entries-archived".format(ContextData.app_name))

    context["form"] = filter_form

    return ContextData.render(request, "form_search.html", context)


def make_bookmarked_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - bookmarked entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    entry = LinkDataController.objects.get(id=pk)

    if LinkDataHyperController.make_bookmarked(request, entry):
        BackgroundJobController.link_archive(entry.link)

    return HttpResponseRedirect(
            reverse("{}:entry-detail".format(ContextData.app_name), kwargs={"pk": entry.pk})
    )


def make_not_bookmarked_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - bookmarked entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    entry = LinkDataController.objects.get(id=pk)
    LinkDataHyperController.make_not_bookmarked(request, entry)

    return HttpResponseRedirect(
            reverse("{}:entry-detail".format(ContextData.app_name), kwargs={"pk": entry.pk})
    )


def download_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - download entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    link = LinkDataController.objects.get(id=pk)

    BackgroundJobController.link_download(subject=link.link)
    summary_text = "Added to queue"

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


def wayback_save(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Waybacksave"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if ConfigurationEntry.get().link_archive:
        link = LinkDataController.objects.get(id=pk)
        BackgroundJobController.link_archive(subject=link.link)

        context["summary_text"] = "Added to waybacksave"
    else:
        context["summary_text"] = "Waybacksave is disabled for links"

    return ContextData.render(request, "summary_present.html", context)


def entry_json(request, pk):
    links = LinkDataController.objects.filter(id=pk)

    if len(links) == 0:
        context["summary_text"] = "No such link in the database {}".format(pk)
        return ContextData.render(request, "summary_present.html", context)

    link = links[0]

    from ..serializers.instanceimporter import InstanceExporter

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

        for view_class in check_views:
            view = view_class()
            view.request = request
            if query_type == view.get_query_type():
                query_filter = view.get_filter()
                query_filter.use_page_limit = True
                found_view = True
                break

    if not found_view:
        view = check_views[0]()
        view.request = request
        query_filter = view.get_filter()
        query_filter.use_page_limit = True

    links = query_filter.get_filtered_objects()

    from ..serializers.instanceimporter import InstanceExporter

    exporter = InstanceExporter()
    json_obj = exporter.export_links(links)

    # JsonResponse
    return JsonResponse(json_obj)


def entries_remove_all(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Remove all entries"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    LinkDataController.objects.all().delete()

    context["summary_text"] = "Removed all entries"

    return ContextData.render(request, "summary_present.html", context)


def entries_remove_nonbookmarked(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Remove nonbookmarked entries"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    LinkDataController.objects.filter(bookmarked=False).delete()

    context["summary_text"] = "Removed all non bookmarked entries"

    return ContextData.render(request, "summary_present.html", context)
