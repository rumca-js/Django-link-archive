from pathlib import Path
import traceback, sys
from datetime import timedelta

from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..prjconfig import Configuration
from ..models import (
    LinkTagsDataModel,
    ConfigurationEntry,
    UserConfig,
    BackgroundJob,
)
from ..models import RssSourceExportHistory
from ..forms import ConfigForm, UserConfigForm
from ..views import ContextData
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
)


def admin_page(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Admin page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    return ContextData.render(request, "admin_page.html", context)


def configuration_page(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Configuration page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ob = ConfigurationEntry.get()

    if request.method == "POST":
        form = ConfigForm(request.POST, instance=ob)
        if form.is_valid():
            form.save()
        else:
            context["summary_text"] = "Form is invalid"
            return ContextData.render(request, "summary_present.html", context)

    ob = ConfigurationEntry.get()
    form = ConfigForm(instance=ob)

    form.method = "POST"
    form.action_url = reverse("{}:configuration".format(ContextData.app_name))

    context["config_form"] = form

    return ContextData.render(request, "configuration.html", context)


def system_status(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Status"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    c = Configuration.get_object()
    context["directory"] = c.directory

    from ..models import YouTubeMetaCache, YouTubeReturnDislikeMetaCache

    context["YouTubeMetaCache"] = len(YouTubeMetaCache.objects.all())
    context["YouTubeReturnDislikeMetaCache"] = len(
        YouTubeReturnDislikeMetaCache.objects.all()
    )
    context["SourceDataModel"] = len(SourceDataController.objects.all())
    context["LinkTagsDataModel"] = len(LinkTagsDataModel.objects.all())
    context["ConfigurationEntry"] = len(ConfigurationEntry.objects.all())
    context["UserConfig"] = len(UserConfig.objects.all())
    context["BackgroundJob"] = len(BackgroundJob.objects.all())

    from ..dateutils import DateUtils

    context["Current_DateTime"] = DateUtils.get_datetime_now_utc()

    from ..models import PersistentInfo

    context["log_items"] = PersistentInfo.get_safe()

    context["server_path"] = Path(".").resolve()
    context["directory"] = Path(".").resolve()

    history = RssSourceExportHistory.get_safe()
    context["export_history_list"] = history

    return ContextData.render(request, "system_status.html", context)


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


def truncate_errors(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - clearing errors"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    from ..models import PersistentInfo

    PersistentInfo.truncate()

    context["summary_text"] = "Clearing errors done"

    return ContextData.render(request, "summary_present.html", context)


def get_incorrect_youtube_links():
    from django.db.models import Q

    criterion1 = Q(link__contains="m.youtube")
    criterion1a = Q(link__contains="youtu.be")

    # only fix those that have youtube in source. leave other RSS sources
    criterion2 = Q(link__contains="https://www.youtube.com")
    criterion3 = Q(source__contains="youtube")
    criterion4 = Q(source__contains="https://www.youtube.com/feeds")

    criterion5 = Q(source__isnull=True)

    entries_no_object = LinkDataController.objects.filter(criterion1 | criterion1a)
    entries_no_object |= LinkDataController.objects.filter(
        criterion2 & criterion3 & ~criterion4
    )
    entries_no_object |= LinkDataController.objects.filter(criterion2 & criterion5)

    if entries_no_object.exists():
        return entries_no_object


def data_errors_page(request):
    def fix_reassign_source_to_nullsource_entries():
        print("fix_reassign_source_to_nullsource_entries")

        entries_no_object = LinkDataController.objects.filter(source_obj=None)
        for entry in entries_no_object:
            source = SourceDataController.objects.filter(url=entry.source)
            if source.exists():
                entry.source_obj = source[0]
                entry.save()
                print("Fixed {0}, added source object".format(entry.link))
        print("fix_reassign_source_to_nullsource_entries done")

    def fix_incorrect_youtube_links_links(entries):
        from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

        for entry in entries:
            print("Fixing: {} {} {}".format(entry.link, entry.title, entry.source))
            h = YouTubeLinkHandler(entry.link)
            h.download_details()

            chan_url = h.get_channel_feed_url()
            link_valid = h.get_link_url()
            if chan_url:
                entry.source = chan_url
                entry.link = link_valid
                entry.save()
                print("Fixed: {} {} {}".format(entry.link, entry.title, chan_url))
            else:
                print("Not fixed: {}".format(entry.link, entry.title))

    def get_tags_for_missing_links():
        result = set()

        tags = LinkTagsDataModel.objects.all()
        for tag in tags:
            if tag.link_obj is None:
                result.add(tag)
                continue

            if tag.link_obj.link != tag.link:
                result.add(tag)
                continue

            if not tag.link_obj.persistent:
                result.add(tag)
                break

        return list(result)

    def get_links_with_incorrect_language():
        from django.db.models import Q

        criterion1 = Q(language__contains="pl")
        criterion2 = Q(language__contains="en")
        criterion3 = Q(language__isnull=True)

        entries_no_object = LinkDataController.objects.filter(
            ~criterion1 & ~criterion2 & ~criterion3, persistent=True
        )

        if entries_no_object.exists():
            return entries_no_object

    context = ContextData.get_context(request)
    context["page_title"] += " - data errors"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    # fix_reassign_source_to_nullsource_entries()
    # fix_tags_links()

    summary_text = "Done"
    try:
        context["links_with_incorrect_language"] = get_links_with_incorrect_language()
        context["incorrect_youtube_links"] = get_incorrect_youtube_links()
        context["tags_for_missing_links"] = get_tags_for_missing_links()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)

    # find links without source

    # remove tags, for which we do not have links, or entry is not bookmarked

    # show bookmarked links without tags

    return ContextData.render(request, "data_errors.html", context)


def fix_reset_youtube_link_details(link_id):
    from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

    entry = LinkDataController.objects.get(id=link_id)

    h = YouTubeLinkHandler(entry.link)
    if not h.download_details():
        return False

    chan_url = h.get_channel_feed_url()
    link_valid = h.get_link_url()

    sources_obj = SourceDataController.objects.filter(url=chan_url)
    source_obj = None
    if len(sources_obj) > 0:
        source_obj = sources_obj[0]

    entry.title = h.get_title()
    entry.description = h.get_description()
    entry.date_published = h.get_datetime_published()
    entry.thumbnail = h.get_thumbnail()
    entry.link = link_valid
    entry.source_obj = source_obj

    if chan_url:
        entry.source = chan_url
    else:
        entry.link = link_valid

    entry.save()

    return True


def fix_reset_youtube_link_details_page(request, pk):
    from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

    context = ContextData.get_context(request)
    context["page_title"] += " - fix youtube links"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    summary_text = ""
    if fix_reset_youtube_link_details(pk):
        summary_text += "Fixed {}".format(pk)
    else:
        summary_text += "Not fixed {}".format(pk)

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


def fix_entry_tags(request, entrypk):
    context = ContextData.get_context(request)
    context["page_title"] += " - fix entry tags"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    entry = LinkDataController.objects.get(id=entrypk)
    tags = entry.tags.all()

    summary_text = ""
    for tag in tags:
        tag.link = tag.link_obj.link
        tag.save()
        summary_text += "Fixed: {}".format(tag.id)

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


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


def show_youtube_link_props(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - show youtube link properties"

    from ..forms import YouTubeLinkSimpleForm

    youtube_link = "https:"
    if not request.method == "POST":
        form = YouTubeLinkSimpleForm(initial={"youtube_link": youtube_link})
        form.method = "POST"
        form.action_url = reverse(
            "{}:show-youtube-link-props".format(ContextData.app_name)
        )
        context["form"] = form

        return ContextData.render(request, "form_basic.html", context)

    else:
        form = YouTubeLinkSimpleForm(request.POST)
        if not form.is_valid():
            context["summary_text"] = "Form is invalid"

            return ContextData.render(request, "summary_present.html", context)
        else:
            from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

            youtube_link = form.cleaned_data["youtube_link"]

            handler = YouTubeLinkHandler(youtube_link)
            handler.download_details()

            yt_json = handler.yt_ob.get_json()
            rd_json = handler.rd_ob.get_json()

            yt_props = str(yt_json)
            rd_props = str(rd_json)

            feed_url = handler.yt_ob.get_channel_feed_url()

            yt_props = [("webpage_url", yt_json["webpage_url"])]
            yt_props.append(("title", yt_json["title"]))
            yt_props.append(("uploader_url", yt_json["uploader_url"]))
            yt_props.append(("channel_url", yt_json["channel_url"]))
            yt_props.append(("channel_feed_url", feed_url))
            yt_props.append(("channel_id", yt_json["channel_id"]))

            for yt_prop in yt_json:
                yt_props.append((yt_prop, str(yt_json[yt_prop])))

            rd_props = []
            for rd_prop in rd_json:
                rd_props.append((rd_prop, str(rd_json[rd_prop])))

            context["youtube_props"] = yt_props
            context["return_dislike_props"] = rd_props

            context["yt_props"] = yt_props
            context["rd_props"] = rd_props

            return ContextData.render(request, "show_youtube_link_props.html", context)


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


def test_page(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - test page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    summary_text = ""

    LinkDataController.move_all_to_archive()

    #items = LinkDataController.objects.filter(source="https://pluralistic.net/feed")
    #items.delete()

    context["summary_text"] = summary_text

    return ContextData.render(request, "summary_present.html", context)


def test_form_page(request):
    from ..forms import OmniSearchForm

    context = ContextData.get_context(request)
    context["page_title"] += " - test form page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    summary_text = ""

    form = OmniSearchForm(request.GET)
    context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def fix_bookmarked_yt(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - fix all"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    summary = ""
    links = LinkDataController.objects.filter(persistent=True)
    for link in links:
        if fix_reset_youtube_link_details(link.id):
            summary += "Fixed: {} {}\n".format(link.link, link.title)
        else:
            summary += "Not Fixed: {} {}\n".format(link.link, link.title)

    context["summary_text"] = summary

    return ContextData.render(request, "summary_present.html", context)


def user_config(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - User configuration"

    if not request.user.is_authenticated:
        return ContextData.render(request, "missing_rights.html", context)

    user_name = request.user.get_username()

    obs = UserConfig.objects.filter(user=user_name)
    if not obs.exists():
        rec = UserConfig(user=user_name)
        rec.save()

    obs = UserConfig.objects.filter(user=user_name)

    if request.method == "POST":
        form = UserConfigForm(request.POST, instance=obs[0])
        if form.is_valid():
            form.save()
        else:
            context["summary_text"] = "user information is not valid, cannot save"
            return ContextData.render(request, "summary_present.html", context)

        obs = UserConfig.objects.filter(user=user_name)
    else:
        form = UserConfigForm(instance=obs[0])

    form.method = "POST"
    form.action_url = reverse("{}:user-config".format(ContextData.app_name))

    context["config_form"] = form

    return ContextData.render(request, "user_configuration.html", context)


def clear_youtube_cache(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - clear youtube cache"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    from ..models import YouTubeMetaCache, YouTubeReturnDislikeMetaCache

    meta = YouTubeMetaCache.objects.all()
    meta.delete()

    dislike = YouTubeReturnDislikeMetaCache.objects.all()
    dislike.delete()

    summary = "Deleted all cache"
    context["summary_text"] = summary

    return ContextData.render(request, "summary_present.html", context)


def download_music(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Download music"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = LinkDataController.objects.filter(id=pk)
    if ft.exists():
        context["summary_text"] = "Added to download queue"
    else:
        context["summary_text"] = "Failed to add to download queue"

    BackgroundJobController.download_music(ft[0])

    return ContextData.render(request, "summary_present.html", context)


def download_video(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Download video"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ft = LinkDataController.objects.filter(id=pk)
    if ft.exists():
        context["summary_text"] = "Added to download queue"
    else:
        context["summary_text"] = "Failed to add to download queue"

    BackgroundJobController.download_video(ft[0])

    return ContextData.render(request, "summary_present.html", context)


class BackgroundJobsView(generic.ListView):
    model = BackgroundJob
    context_object_name = "jobs_list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BackgroundJobsView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        context["BackgroundJob"] = len(BackgroundJob.objects.all())

        return context


def backgroundjob_remove(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Background job remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    bg = BackgroundJob.objects.get(id=pk)
    bg.delete()

    context["summary_text"] = "Background job has been removed"

    return ContextData.render(request, "summary_present.html", context)


def backgroundjobs_remove(request, job_type):
    context = ContextData.get_context(request)
    context["page_title"] += " - Background jobs remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    jobs = BackgroundJob.objects.filter(job=job_type)
    jobs.delete()

    context["summary_text"] = "Background jobs has been removed"

    return ContextData.render(request, "summary_present.html", context)
