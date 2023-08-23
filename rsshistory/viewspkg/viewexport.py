from datetime import timedelta

from django.views import generic
from django.urls import reverse

from ..models import DataExport
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
)
from ..views import ContextData
from ..forms import DataExportForm


def import_reading_list_view(request):
    from ..serializers.readinglist import ReadingList
    from ..webtools import Page

    context = ContextData.get_context(request)
    context["page_title"] += " - import view"

    c = Configuration.get_object()
    import_path = c.get_import_path() / "readingList.csv"

    summary_text = ""

    rlist_data = import_path.read_text()

    rlist = ReadingList(import_path)

    for entry in rlist.entries:
        try:
            print(entry["title"])

            objs = LinkDataController.objects.filter(link=entry["url"])
            if objs.exists():
                print(entry["title"] + ", Skipping")
                summary_text += (
                    entry["title"] + " " + entry["url"] + ": Skipping, already in DB\n"
                )
                continue
            else:
                p = Page(entry["url"])
                if not p.get_domain():
                    summary_text += (
                        entry["title"]
                        + " "
                        + entry["url"]
                        + ": NOK - could not find domain\n"
                    )
                    continue

                lang = p.get_language()
                if not lang:
                    summary_text += (
                        entry["title"]
                        + " "
                        + entry["url"]
                        + ": NOK - could not find language\n"
                    )
                    continue

                ent = LinkDataController(
                    source=p.get_domain(),
                    title=entry["title"],
                    description=entry["description"],
                    link=entry["url"],
                    date_published=entry["date"],
                    persistent=True,
                    dead=False,
                    user="Thomas Pain",
                    language=lang,
                    thumbnail=entry["image"],
                )

                ent.save()

                summary_text += entry["title"] + " " + entry["url"] + ": OK \n"
        except Exception as e:
            summary_text += entry["title"] + " " + entry["url"] + ": NOK \n"

    context["summary_text"] = summary_text
    return ContextData.render(request, "summary_present.html", context)


def import_from_instance(request):
    from ..forms import LinkInputForm

    context = ContextData.get_context(request)
    context["page_title"] += " - Import from instance"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = LinkInputForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data["link"]

            from ..serializers.instanceimporter import InstanceImporter

            ie = InstanceImporter(link)
            ie.import_all()

            context["summary_text"] = "Imported"
            return ContextData.render(request, "summary_present.html", context)

        else:
            context["summary_text"] = "Form is invalid"
            return ContextData.render(request, "summary_present.html", context)

    else:
        form = LinkInputForm()
        form.method = "POST"

        context["form_title"] = "Instance URL import"
        context[
            "form_description_pre"
        ] = "Provide URL to another instance od Django-link-archive, the link of JSON data."
        context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def get_time_stamps(url, start_time, stop_time):
    time = stop_time
    while time >= start_time:
        yield time
        time -= timedelta(days=1)


def import_source_from_ia_range_impl(source_url, archive_start, archive_stop):
    from ..services.waybackmachine import WaybackMachine

    wb = WaybackMachine()

    for timestamp in get_time_stamps(source_url, archive_start, archive_stop):
        archive_url = wb.get_archive_url(source_url, timestamp)
        if not archive_url:
            print(
                "Could not find archive link for timestamp {0} {1}".format(
                    source_url, timestamp
                )
            )
            continue

        print("Processing {0} {1} {2}".format(timestamp, source_url, archive_url))

        if import_source_from_ia_impl(wb, source_url, archive_url, timestamp) == False:
            print(
                "Could not import feed for time: {0} {1} {2}".format(
                    source_url, archive_url, timestamp
                )
            )


def import_source_from_ia(request, pk):
    from ..forms import ImportSourceRangeFromInternetArchiveForm

    context = ContextData.get_context(request)
    context["page_title"] += " - Import internet archive"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = ImportSourceRangeFromInternetArchiveForm(request.POST)
        if form.is_valid():
            source_url = form.cleaned_data["source_url"]
            archive_start = form.cleaned_data["archive_start"]
            archive_stop = form.cleaned_data["archive_stop"]

            if (
                import_source_from_ia_range_impl(
                    source_url, archive_start, archive_stop
                )
                == False
            ):
                context["summary_text"] = "Could not read internet archive"
                return ContextData.render(request, "summary_present.html", context)
            else:
                context["summary_text"] = "Internet archive data read successfully"
                return ContextData.render(request, "summary_present.html", context)

    source_obj = SourceDataController.objects.get(id=pk)

    form = ImportSourceRangeFromInternetArchiveForm(
        initial={
            "source_url": source_obj.url,
            "archive_start": date.today() - timedelta(days=1),
            "archive_stop": date.today(),
        }
    )
    form.method = "POST"

    context["form"] = form

    return ContextData.render(request, "import_internetarchive.html", context)


def import_source_from_ia_impl(wb, source_url, source_archive_url, archive_time):
    print("Reading from time: {0} {1}".format(source_url, archive_time))

    source_obj = SourceDataController.objects.filter(url=source_url)[0]

    c = Configuration.get_object()

    from ..pluginsources.rsssourceprocessor import RssSourceProcessor

    proc = RssSourceProcessor(c)
    proc.allow_adding_with_current_time = False
    proc.default_entry_timestamp = archive_time
    entries = proc.process_rss_source(source_obj, source_archive_url)

    if entries == 0:
        print("No entry read")
        return False

    print("Internet archive done {0}".format(source_url))

    return True


def write_bookmarks(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Writer bookmarks"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    BackgroundJobController.write_bookmarks()

    context["summary_text"] = "Wrote job started"

    return ContextData.render(request, "summary_present.html", context)


def import_bookmarks(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Import bookmarks"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    BackgroundJobController.import_bookmarks()

    context["summary_text"] = "Import job started"

    return ContextData.render(request, "summary_present.html", context)


def import_sources(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Import sources"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    BackgroundJobController.import_sources()

    context["summary_text"] = "Import job started"

    return ContextData.render(request, "summary_present.html", context)


def write_daily_data_form(request):
    from ..forms import ExportDailyDataForm

    context = ContextData.get_context(request)
    context["page_title"] += " - Write daily data"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = ExportDailyDataForm(request.POST)
        if form.is_valid():
            time_start = form.cleaned_data["time_start"]
            time_stop = form.cleaned_data["time_stop"]

            if BackgroundJobController.write_daily_data_range(time_start, time_stop):
                context[
                    "summary_text"
                ] = "Added daily write job. Start:{} Stop:{}".format(
                    time_start, time_stop
                )
            else:
                context["summary_text"] = "Form is invalid. Start:{} Stop:{}".format(
                    time_start, time_stop
                )
            return ContextData.render(request, "summary_present.html", context)

    from ..dateutils import DateUtils

    date = DateUtils.get_date_today()

    form = ExportDailyDataForm(
        initial={
            "time_start": date.today() - timedelta(days=1),
            "time_stop": date.today(),
        }
    )
    form.method = "POST"

    context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def import_daily_data(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Import daily data"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    BackgroundJobController.import_daily_data()

    context["summary_text"] = "Import job started"

    return ContextData.render(request, "summary_present.html", context)


def write_tag_form(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - tags writer"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    from ..forms import ExportTopicForm

    if request.method == "POST":
        form = ExportTopicForm(request.POST)
        if form.is_valid():
            tag = form.cleaned_data["tag"]

            if BackgroundJobController.write_tag_data(tag):
                context["summary_text"] = "Added daily write job. Tag:{}".format(tag)
            else:
                context["summary_text"] = "Form is invalid. Tag:{}".format(tag)
            return ContextData.render(request, "summary_present.html", context)

    form = ExportTopicForm()
    form.method = "POST"

    context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def push_daily_data_form(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - tags writer"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    from ..forms import PushDailyDataForm

    if request.method == "POST":
        form = PushDailyDataForm(request.POST)
        if form.is_valid():
            input_date = form.cleaned_data["input_date"]

            if BackgroundJobController.push_daily_data_to_repo(input_date.isoformat()):
                context["summary_text"] = "Added daily data push job. Tag:{}".format(
                    input_date.isoformat()
                )
            else:
                context["summary_text"] = "Form is invalid. Tag:{}".format(tag)
            return ContextData.render(request, "summary_present.html", context)

    form = PushDailyDataForm()
    form.method = "POST"

    context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def data_export_add(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Data export add page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = DataExportForm(request.POST)
        if form.is_valid():
            form.save()
        else:
            context["summary_text"] = "Form is invalid"
            return ContextData.render(request, "summary_present.html", context)

    form = DataExportForm()
    form.method = "POST"
    form.action_url = reverse("{}:data-export-add".format(ContextData.app_name))

    context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def data_export_edit(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Data export edit page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    objs = DataExport.objects.filter(id=pk)
    if len(objs) == 0:
        context["summary_text"] = "No such object"
        return ContextData.render(request, "summary_present.html", context)

    if request.method == "POST":
        form = DataExportForm(request.POST, instance=objs[0])
        if form.is_valid():
            form.save()
        else:
            context["summary_text"] = "Form is invalid"
            return ContextData.render(request, "summary_present.html", context)

    form = DataExportForm(instance=objs[0])
    form.method = "POST"
    form.action_url = reverse(
        "{}:data-export-edit".format(ContextData.app_name), args=[pk]
    )

    context["config_form"] = form

    return ContextData.render(request, "configuration.html", context)


def data_export_remove(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Data export remove page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    objs = DataExport.objects.filter(id=pk)
    if len(objs) == 0:
        context["summary_text"] = "No such object"
        return ContextData.render(request, "summary_present.html", context)
    else:
        objs.delete()
        context["summary_text"] = "Removed object"
        return ContextData.render(request, "summary_present.html", context)


class DataExportListView(generic.ListView):
    model = DataExport
    context_object_name = "objects"
    paginate_by = 100

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(DataExportListView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        return context


class DataExportDetailsView(generic.DetailView):
    model = DataExport
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(DataExportDetailsView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        return context
