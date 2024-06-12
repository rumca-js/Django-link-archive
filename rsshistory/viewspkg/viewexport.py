from datetime import timedelta

from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

from ..apps import LinkDatabase
from ..models import DataExport, ConfigurationEntry
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
)
from ..views import ViewPage
from ..forms import DataExportForm
from ..webtools import DomainAwarePage


def import_reading_list_view(request):
    from ..serializers import ReadingListFile

    page = ViewPage(request)
    page.set_title("Import view")
    data = page.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    c = Configuration.get_object()
    import_path = c.get_import_path() / "readingList.csv"

    summary_text = ""

    rlist_data = import_path.read_text()

    rlist = ReadingListFile(import_path)

    for entry in rlist.get_entries():
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
                p = DomainAwarePage(entry["url"])
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
                    bookmarked=True,
                    dead=False,
                    user="Thomas Pain",
                    language=lang,
                    thumbnail=entry["image"],
                )

                ent.save()

                summary_text += entry["title"] + " " + entry["url"] + ": OK \n"
        except Exception as e:
            summary_text += entry["title"] + " " + entry["url"] + ": NOK \n"

    page.context["summary_text"] = summary_text
    return page.render("summary_present.html")


def import_from_instance(request):
    from ..forms import LinkInputForm

    p = ViewPage(request)
    p.set_title("Import from another instance")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = LinkInputForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data["link"]

            BackgroundJobController.import_from_instance(link, request.user.username)

            p.context["summary_text"] = "Import job added"
            return p.render("summary_present.html")

        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    else:
        form = LinkInputForm()
        form.method = "POST"

        p.context["form_title"] = "Instance URL import"
        p.context[
            "form_description_pre"
        ] = "Provide URL to another instance od Django-link-archive, the link of JSON data."
        p.context["form"] = form

    return p.render("form_basic.html")


def import_from_files(request):
    from ..forms import ImportFromFilesForm

    p = ViewPage(request)
    p.set_title("Import from files")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = ImportFromFilesForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            BackgroundJobController.import_from_files(data)

            p.context["summary_text"] = "Import job added"
            return p.render("summary_present.html")

        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    else:
        form = ImportFromFilesForm()
        form.method = "POST"

        p.context["form_title"] = "Import from files"
        p.context["form_description_pre"] = "Provide detail about the import."
        p.context["form"] = form

    return p.render("form_basic.html")


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

    p = ViewPage(request)
    p.set_title("Import from internet archive")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

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
                p.context["summary_text"] = "Could not read internet archive"
                return p.render("summary_present.html")
            else:
                p.context["summary_text"] = "Internet archive data read successfully"
                return p.render("summary_present.html")

    source_obj = SourceDataController.objects.get(id=pk)

    form = ImportSourceRangeFromInternetArchiveForm(
        initial={
            "source_url": source_obj.url,
            "archive_start": date.today() - timedelta(days=1),
            "archive_stop": date.today(),
        }
    )
    form.method = "POST"

    p.context["form"] = form

    return p.render("import_internetarchive.html")


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
    p = ViewPage(request)
    p.set_title("Write bookmarks")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    BackgroundJobController.write_bookmarks()

    p.context["summary_text"] = "Wrote job started"

    return p.render("summary_present.html")


def import_bookmarks(request):
    p = ViewPage(request)
    p.set_title("Import bookmarks")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    BackgroundJobController.import_bookmarks()

    p.context["summary_text"] = "Import job started"

    return p.render("summary_present.html")


def import_sources(request):
    p = ViewPage(request)
    p.set_title("Import sources")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    BackgroundJobController.import_sources()

    p.context["summary_text"] = "Import job started"

    return p.render("summary_present.html")


def data_export_job_add(request, pk):
    p = ViewPage(request)
    p.set_title("Add job to export data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    exports = DataExport.objects.filter(id=pk)
    if exports.count() == 0:
        p.context["summary_text"] = "No such export"
        return p.render("summary_present.html")

    export = exports[0]

    BackgroundJobController.export_data(export)

    return redirect("{}:data-exports".format(LinkDatabase.name))


def write_daily_data_form(request):
    from ..forms import ExportDailyDataForm

    p = ViewPage(request)
    p.set_title("Write daily data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = ExportDailyDataForm(request.POST)
        if form.is_valid():
            time_start = form.cleaned_data["time_start"]
            time_stop = form.cleaned_data["time_stop"]

            if BackgroundJobController.write_daily_data_range(time_start, time_stop):
                p.context[
                    "summary_text"
                ] = "Added daily write job. Start:{} Stop:{}".format(
                    time_start, time_stop
                )
            else:
                p.context["summary_text"] = "Form is invalid. Start:{} Stop:{}".format(
                    time_start, time_stop
                )
            return p.render("summary_present.html")

    from ..dateutils import DateUtils

    date = DateUtils.get_date_today()

    form = ExportDailyDataForm(
        initial={
            "time_start": date.today() - timedelta(days=1),
            "time_stop": date.today(),
        }
    )
    form.method = "POST"

    p.context["form"] = form

    return p.render("form_basic.html")


def import_daily_data(request):
    p = ViewPage(request)
    p.set_title("Import daily data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    BackgroundJobController.import_daily_data()

    p.context["summary_text"] = "Import job started"

    return p.render("summary_present.html")


def write_tag_form(request):
    p = ViewPage(request)
    p.set_title("Write tags")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..forms import ExportTopicForm

    if request.method == "POST":
        form = ExportTopicForm(request.POST)
        if form.is_valid():
            tag = form.cleaned_data["tag"]

            if BackgroundJobController.write_tag_data(tag):
                p.context["summary_text"] = "Added daily write job. Tag:{}".format(tag)
            else:
                p.context["summary_text"] = "Form is invalid. Tag:{}".format(tag)
            return p.render("summary_present.html")

    form = ExportTopicForm()
    form.method = "POST"

    p.context["form"] = form

    return p.render("form_basic.html")


def push_daily_data_form(request):
    p = ViewPage(request)
    p.set_title("Push daily data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..forms import PushDailyDataForm

    if request.method == "POST":
        form = PushDailyDataForm(request.POST)
        if form.is_valid():
            input_date = form.cleaned_data["input_date"]

            if BackgroundJobController.push_daily_data_to_repo(input_date.isoformat()):
                p.context["summary_text"] = "Added daily data push job. Tag:{}".format(
                    input_date.isoformat()
                )
            else:
                p.context["summary_text"] = "Form is invalid. Tag:{}".format(tag)
            return p.render("summary_present.html")

    form = PushDailyDataForm()
    form.method = "POST"

    p.context["form"] = form

    return p.render("form_basic.html")


def data_export_add(request):
    p = ViewPage(request)
    p.set_title("Add data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = DataExportForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("{}:data-exports".format(LinkDatabase.name)))
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = DataExportForm()
    form.method = "POST"
    form.action_url = reverse("{}:data-export-add".format(LinkDatabase.name))

    p.context["form"] = form

    return p.render("form_basic.html")


def data_export_edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = DataExport.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")

    if request.method == "POST":
        form = DataExportForm(request.POST, instance=objs[0])
        if form.is_valid():
            form.save()
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = DataExportForm(instance=objs[0])
    form.method = "POST"
    form.action_url = reverse(
        "{}:data-export-edit".format(LinkDatabase.name), args=[pk]
    )

    p.context["config_form"] = form

    return p.render("configuration.html")


def data_export_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove data export")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    objs = DataExport.objects.filter(id=pk)
    if objs.count() == 0:
        p.context["summary_text"] = "No such object"
        return p.render("summary_present.html")
    else:
        objs.delete()
        p.context["summary_text"] = "Removed object"
        return p.render("summary_present.html")


class DataExportListView(generic.ListView):
    model = DataExport
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(DataExportListView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(DataExportListView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        return context


class DataExportDetailsView(generic.DetailView):
    model = DataExport
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(DataExportDetailsView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        return context
