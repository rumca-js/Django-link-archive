from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.db.models import Q

from ..models import (
    LinkTagsDataModel,
    BackgroundJob,
    ConfigurationEntry,
)
from ..prjconfig import Configuration
from ..forms import (
    EntryForm,
    EntryChoiceForm,
    ConfigForm,
    BasicEntryChoiceForm,
    EntryBookmarksChoiceForm,
)
from ..forms import EntryChoiceArgsExtractor
from ..views import ContextData
from ..controllers import (
    LinkDataController,
    SourceDataController,
    BackgroundJobController,
)


class EntriesSearchListView(generic.ListView):
    model = LinkDataController
    context_object_name = "entries_list"
    paginate_by = 100

    def get_queryset(self):
        self.extractor = EntryChoiceArgsExtractor(self.request.GET)
        self.extractor.get_sources()
        return self.extractor.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(EntriesSearchListView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)
        # Create any data and add it to the context

        context["page_title"] += " - entries"

        queue_size = BackgroundJobController.get_number_of_jobs(
            BackgroundJob.JOB_PROCESS_SOURCE
        )
        context["rss_are_fetched"] = queue_size > 0
        context["rss_queue_size"] = queue_size

        adict = self.extractor.get_entry_filter_args()

        self.filter_form = EntryChoiceForm(adict)
        self.filter_form.create(self.extractor.sources)
        self.filter_form.is_valid()

        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse("{}:entries".format(ContextData.app_name))

        context["args_extractor"] = self.extractor
        context["reset_link"] = reverse(
            "{}:entries-search-init".format(ContextData.app_name)
        )

        context["filter_form"] = self.filter_form
        if "search" in self.request.GET:
            context["search_term"] = self.request.GET["search"]
        elif "tag" in self.request.GET:
            context["search_term"] = self.request.GET["tag"]

        return context


class EntriesRecentListView(generic.ListView):
    model = LinkDataController
    context_object_name = "entries_list"
    paginate_by = 100

    def get_queryset(self):
        self.extractor = EntryChoiceArgsExtractor(self.request.GET)
        self.extractor.get_sources()
        return self.extractor.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(EntriesRecentListView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)
        # Create any data and add it to the context

        context["page_title"] += " - entries"

        queue_size = BackgroundJobController.get_number_of_jobs(
            BackgroundJob.JOB_PROCESS_SOURCE
        )
        context["rss_are_fetched"] = queue_size > 0
        context["rss_queue_size"] = queue_size

        adict = self.extractor.get_entry_filter_args()

        self.filter_form = BasicEntryChoiceForm(adict)
        self.filter_form.create(self.extractor.sources)

        self.filter_form.is_valid()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse(
            "{}:entries-recent".format(ContextData.app_name)
        )

        context["args_extractor"] = self.extractor
        context["reset_link"] = reverse(
            "{}:entries-recent-init".format(ContextData.app_name)
        )

        context["filter_form"] = self.filter_form
        if "search" in self.request.GET:
            context["search_term"] = self.request.GET["search"]
        elif "tag" in self.request.GET:
            context["search_term"] = self.request.GET["tag"]

        return context


class EntriesNotTaggedView(generic.ListView):
    # TODO inherit from entries view?
    model = LinkDataController
    context_object_name = "entries_list"
    paginate_by = 100
    template_name = ContextData.get_full_template("linkdatacontroller_list.html")

    def get_queryset(self):
        self.extractor = EntryChoiceArgsExtractor(self.request.GET)
        self.extractor.get_sources()
        return self.extractor.get_filtered_objects(
            Q(tags__tag__isnull=True, persistent=True)
        )

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(EntriesNotTaggedView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)
        # Create any data and add it to the context

        context["page_title"] += " - not bookmarked"

        queue_size = BackgroundJobController.get_number_of_jobs(
            BackgroundJob.JOB_PROCESS_SOURCE
        )
        context["rss_are_fetched"] = queue_size > 0
        context["rss_queue_size"] = queue_size

        adict = self.extractor.get_entry_filter_args()

        self.filter_form = EntryChoiceForm(adict)
        self.filter_form.create(self.extractor.sources)

        self.filter_form.is_valid()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse(
            "{}:entries-untagged".format(ContextData.app_name)
        )

        context["args_extractor"] = self.extractor
        context["reset_link"] = reverse(
            "{}:entries-untagged".format(ContextData.app_name)
        )
        context["filter_form"] = self.filter_form

        return context


class EntriesBookmarkedView(generic.ListView):
    # TODO inherit from entries view?
    model = LinkDataController
    context_object_name = "entries_list"
    paginate_by = 100
    template_name = ContextData.get_full_template("linkdatacontroller_list.html")

    def get_queryset(self):
        self.extractor = EntryChoiceArgsExtractor(self.request.GET)
        self.extractor.set_time_constrained(False)
        self.extractor.get_sources()
        return self.extractor.get_filtered_objects(Q(persistent=True))

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(EntriesBookmarkedView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)
        # Create any data and add it to the context

        context["page_title"] += " - not bookmarked"

        queue_size = BackgroundJobController.get_number_of_jobs(
            BackgroundJob.JOB_PROCESS_SOURCE
        )
        context["rss_are_fetched"] = queue_size > 0
        context["rss_queue_size"] = queue_size

        adict = self.extractor.get_entry_filter_args()

        self.filter_form = EntryBookmarksChoiceForm(adict)
        self.filter_form.create(self.extractor.sources)

        self.filter_form.is_valid()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse(
            "{}:entries-bookmarked".format(ContextData.app_name)
        )

        context["args_extractor"] = self.extractor
        context["reset_link"] = reverse(
            "{}:entries-bookmarked-init".format(ContextData.app_name)
        )
        context["filter_form"] = self.filter_form

        return context


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

        data = LinkDataController.get_full_information(form.get_information())
        if valid:
            if not form.save_form(data):
                context["summary_text"] = "Could not save link"
                return ContextData.render(request, "summary_present.html", context)

            context["form"] = form

            ob = LinkDataController.objects.filter(link=data["link"])
            if ob.exists():
                context["entry"] = ob[0]

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


def make_persistent_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - persistent entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    entry = LinkDataController.objects.get(id=pk)

    prev_state = entry.persistent

    entry.persistent = True
    entry.user = request.user.username
    entry.save()

    if prev_state != True:
        BackgroundJobController.link_archive(entry.link)

    summary_text = "Link changed to state: " + str(entry.persistent)

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


def make_not_persistent_entry(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - persistent entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = LinkDataController.objects.get(id=pk)
    ft.make_not_persistent(request.user.username)

    summary_text = "Link changed to state: " + str(ft.persistent)

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


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
