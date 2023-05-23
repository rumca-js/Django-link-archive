from pathlib import Path
import traceback, sys

from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..prjconfig import Configuration
from ..models import SourceDataModel, LinkDataModel, LinkTagsDataModel, ConfigurationEntry, UserConfig
from ..models import RssSourceImportHistory, RssSourceExportHistory
from ..forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, CommentEntryForm
from ..forms import ConfigForm, UserConfigForm


def init_context(context):
    from ..views import init_context
    return init_context(context)

def get_context(request):
    from ..views import get_context
    return get_context(request)

def get_app():
    from ..views import app_name
    return app_name


def configuration(request):
    context = get_context(request)
    context['page_title'] += " - Configuration"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)
    
    ob = ConfigurationEntry.objects.all()
    if not ob.exists():
        rec = ConfigurationEntry()
        rec.save()

    ob = ConfigurationEntry.objects.all()

    if request.method == 'POST':
        obs = ConfigurationEntry.objects.all()
        if len(obs) > 0:
            form = ConfigForm(request.POST, instance=obs[0])
        else:
            form = ConfigForm(request.POST)
        if form.is_valid():
            form.save()

    obs = ConfigurationEntry.objects.all()
    
    if len(obs) > 0:
        form = ConfigForm(instance = obs[0])
    else:
        form = ConfigForm()

    form.method = "POST"
    form.action_url = reverse('rsshistory:configuration')

    context['config_form'] = form

    return render(request, get_app() / 'configuration.html', context)


def system_status(request):
    context = get_context(request)
    context['page_title'] += " - Status"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)
    
    c = Configuration.get_object(str(get_app()))

    #size_b = get_directory_size_bytes(c.directory)
    #size_kb = size_b / 1024
    #size_mb = size_kb / 1024

    context['directory'] = c.directory
    #context['database_size_bytes'] = size_b
    #context['database_size_kbytes'] = size_kb
    #context['database_size_mbytes'] = size_mb

    from ..models import YouTubeMetaCache, YouTubeReturnDislikeMetaCache
    context['YouTubeMetaCache'] = len(YouTubeMetaCache.objects.all())
    context['YouTubeReturnDislikeMetaCache'] = len(YouTubeReturnDislikeMetaCache.objects.all())
    context['SourceDataModel'] = len(SourceDataModel.objects.all())
    context['LinkTagsDataModel'] = len(LinkTagsDataModel.objects.all())

    from ..models import PersistentInfo
    context['log_items'] = PersistentInfo.objects.all()

    threads = c.get_threads()
    if threads:
        for thread in threads:
            items = thread.get_processs_list()
            context['thread_list'] = threads

    context['server_path'] = Path(".").resolve()
    context['directory'] = Path(".").resolve()

    history = RssSourceImportHistory.objects.all()[:100]
    context['import_history_list'] = history

    history = RssSourceExportHistory.objects.all()[:100]
    context['export_history_list'] = history

    return render(request, get_app() / 'system_status.html', context)


def start_threads(request):
    context = get_context(request)
    context['page_title'] += " - Status"

    c = Configuration.get_object(str(get_app()))
    c.create_threads()

    context["summary_text"] = "Threads started"

    return render(request, get_app() / 'summary_present.html', context)


def import_view(request):
    from ..serializers.readinglist import ReadingList
    from ..webtools import Page

    context = get_context(request)
    context['page_title'] += " - import view"

    c = Configuration.get_object(str(get_app()))
    import_path = c.get_import_path() / 'readingList.csv'

    summary_text = ""

    rlist_data = import_path.read_text()

    rlist = ReadingList(import_path)

    for entry in rlist.entries:
        try:
            print(entry['title'])

            objs = LinkDataModel.objects.filter(link = entry['url'])
            if objs.exists():
                print(entry['title'] + ", Skipping")
                summary_text += entry['title'] + " " + entry['url'] + ": Skipping, already in DB\n"
                continue
            else:
                p = Page(entry['url'])
                if not p.get_domain():
                    summary_text += entry['title'] + " " + entry['url'] + ": NOK - could not find domain\n"
                    continue

                lang = p.get_language()
                if not lang:
                    summary_text += entry['title'] + " " + entry['url'] + ": NOK - could not find language\n"
                    continue

                ent = LinkDataModel(
                        source = p.get_domain(),
                        title = entry['title'],
                        description = entry['description'],
                        link = entry['url'],
                        date_published = entry['date'],
                        persistent = True,
                        dead = False,
                        user = "Thomas Pain",
                        language = lang)

                ent.save()

                summary_text += entry['title'] + " " + entry['url'] + ": OK \n"
        except Exception as e:
            summary_text += entry['title'] + " " + entry['url'] + ": NOK \n"

    context["summary_text"] = summary_text
    return render(request, get_app() / 'summary_present.html', context)


def truncate_errors(request):
    context = get_context(request)
    context['page_title'] += " - clearing errors"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    from ..models import PersistentInfo
    PersistentInfo.truncate()

    context["summary_text"] = "Clearing errors done"

    return render(request, get_app() / 'summary_present.html', context)


def get_incorrect_youtube_links():
    from django.db.models import Q
    criterion1 = Q(link__contains="m.youtube")
    criterion1a = Q(link__contains="youtu.be")

    # only fix those that have youtube in source. leave other RSS sources
    criterion2 = Q(link__contains="https://www.youtube.com")
    criterion3 = Q(source__contains="youtube")
    criterion4 = Q(source__contains="https://www.youtube.com/feeds")

    criterion5 = Q(source__isnull = True)
    criterion6 = Q(source_obj__isnull = True)

    entries_no_object = LinkDataModel.objects.filter(criterion1 | criterion1a)
    entries_no_object |= LinkDataModel.objects.filter(criterion2 & criterion3 & ~criterion4)
    entries_no_object |= LinkDataModel.objects.filter(criterion2 & criterion5)
    #entries_no_object |= LinkDataModel.objects.filter(criterion2 & ~criterion5 & criterion6)

    if entries_no_object.exists():
        return entries_no_object


def data_errors_page(request):

    def fix_reassign_source_to_nullsource_entries():
        print("fix_reassign_source_to_nullsource_entries")

        entries_no_object = LinkDataModel.objects.filter(source_obj = None)
        for entry in entries_no_object:
            source = SourceDataModel.objects.filter(url = entry.source)
            if source.exists():
                entry.source_obj = source[0]
                entry.save()
                #summary_text += "Fixed {0}, added source object\n".format(entry.link)
                print("Fixed {0}, added source object".format(entry.link))
        print("fix_reassign_source_to_nullsource_entries done")

    def fix_incorrect_youtube_links_links(entries):
        from ..handlers.youtubelinkhandler import YouTubeLinkHandler

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
        criterion3 = Q(language__isnull = True)

        entries_no_object = LinkDataModel.objects.filter(~criterion1 & ~criterion2 & ~criterion3, persistent = True)

        if entries_no_object.exists():
            return entries_no_object

    context = get_context(request)
    context['page_title'] += " - data errors"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    #fix_reassign_source_to_nullsource_entries()
    #fix_tags_links()

    summary_text = "Done"
    try:
        context['links_with_incorrect_language'] = get_links_with_incorrect_language()
        context['incorrect_youtube_links'] = get_incorrect_youtube_links()
        context['tags_for_missing_links'] = get_tags_for_missing_links()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)

    # find links without source

    # remove tags, for which we do not have links, or entry is not bookmarked

    # show bookmarked links without tags

    return render(request, get_app() / 'data_errors.html', context)


def fix_reset_youtube_link_details(link_id):
    from ..handlers.youtubelinkhandler import YouTubeLinkHandler

    entry = LinkDataModel.objects.get(id = link_id)

    h = YouTubeLinkHandler(entry.link)
    if not h.download_details():
        return False

    chan_url = h.get_channel_feed_url()
    link_valid = h.get_link_url()

    sources_obj = SourceDataModel.objects.filter(url = chan_url)
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
    from ..handlers.youtubelinkhandler import YouTubeLinkHandler

    context = get_context(request)
    context['page_title'] += " - fix youtube links"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    summary_text = ""
    if fix_reset_youtube_link_details(pk):
        summary_text += "Fixed {}".format(pk)
    else:
        summary_text += "Not fixed {}".format(pk)

    context['summary_text'] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def fix_source_entries_language(request, pk):
    from ..handlers.youtubelinkhandler import YouTubeLinkHandler

    context = get_context(request)
    context['page_title'] += " - fix source entries language"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    source_obj = SourceDataModel.objects.get(id = pk)

    summary_text = ""
    for entry in source_obj.entries.all():
        if entry.language != source_obj.language:
            entry.language = source_obj.language
            entry.save()
            summary_text += entry.title + " " + entry.link + "\n"

    context['summary_text'] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def fix_entry_tags(request, entrypk):

    context = get_context(request)
    context['page_title'] += " - fix entry tags"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    entry = LinkDataModel.objects.get(id = entrypk)
    tags = entry.tags.all()

    summary_text = ""
    for tag in tags:
        tag.link = tag.link_obj.link
        tag.save()
        summary_text += "Fixed: {}".format(tag.id)

    context['summary_text'] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def get_time_stamps(url, start_time, stop_time):

   time = stop_time
   while time >= start_time:
       if len(RssSourceImportHistory.objects.filter(url = url, date = time)) != 0:
           time -= timedelta(days = 1)
           print("Skipping already imported timestamp {0} {1}".format(url, time))
           continue

       yield time
       time -= timedelta(days = 1)

def import_source_from_ia_range_impl(source_url, archive_start, archive_stop):
    from ..sources.waybackmachine import WaybackMachine
    wb = WaybackMachine()

    for timestamp in get_time_stamps(source_url, archive_start, archive_stop):
        archive_url = wb.get_archive_url(source_url, timestamp)
        if not archive_url:
            print("Could not find archive link for timestamp {0} {1}".format(source_url, timestamp))
            continue

        print("Processing {0} {1} {2}".format(timestamp, source_url, archive_url))

        if import_source_from_ia_impl(wb, source_url, archive_url, timestamp) == False:
            print("Could not import feed for time: {0} {1} {2}".format(source_url, archive_url, timestamp))


def import_source_from_ia(request, pk):
    from ..forms import ImportSourceRangeFromInternetArchiveForm

    context = get_context(request)
    context['page_title'] += " - Import internet archive"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    if request.method == 'POST':
        form = ImportSourceRangeFromInternetArchiveForm(request.POST)
        if form.is_valid():
            source_url = form.cleaned_data['source_url']
            archive_start = form.cleaned_data['archive_start']
            archive_stop = form.cleaned_data['archive_stop']

            if import_source_from_ia_range_impl(source_url, archive_start, archive_stop) == False:
                context["summary_text"] = "Could not read internet archive"
                return render(request, get_app() / 'summary_present.html', context)
            else:
                context["summary_text"] = "Internet archive data read successfully"
                return render(request, get_app() / 'summary_present.html', context)
    
    source_obj = SourceDataModel.objects.get(id = pk)
    
    form = ImportSourceRangeFromInternetArchiveForm(initial={"source_url": source_obj.url, 
             'archive_start' : date.today() - timedelta(days = 1),
             'archive_stop' : date.today()})
    form.method = "POST"
    #form.action_url = reverse('rsshistory:configuration')

    context['form'] = form

    return render(request, get_app() / 'import_internetarchive.html', context)


def import_source_from_ia_impl(wb, source_url, source_archive_url, archive_time):
    print("Reading from time: {0} {1}".format(source_url, archive_time))

    source_obj = SourceDataModel.objects.filter(url = source_url)[0]

    if len(RssSourceImportHistory.objects.filter(url = source_obj.url, date = archive_time)) != 0:
        print("Import timestamp exists")
        return False

    c = Configuration.get_object(str(get_app()))

    from ..sources.rsssourceprocessor import RssSourceProcessor

    proc = RssSourceProcessor(c)
    proc.allow_adding_with_current_time = False
    proc.default_entry_timestamp = archive_time
    entries = proc.process_rss_source(source_obj, source_archive_url)

    if entries == 0:
        print("No entry read")
        return False

    print("Internet archive done {0}".format(source_url))

    if len(RssSourceImportHistory.objects.filter(url = source_obj.url, date = archive_time)) == 0:
        history = RssSourceImportHistory(url = source_obj.url, date = archive_time, source_obj = source_obj)
        history.save()

    return True

def show_youtube_link_props(request):
    context = get_context(request)
    context['page_title'] += " - show youtube link properties"

    from ..forms import YouTubeLinkSimpleForm

    youtube_link = "https:"
    if not request.method == 'POST':
        form = YouTubeLinkSimpleForm(initial={'youtube_link' : youtube_link})
        form.method = "POST"
        form.action_url = reverse('rsshistory:show-youtube-link-props')
        context['form'] = form

        return render(request, get_app() / 'form_basic.html', context)

    else:
        form = YouTubeLinkSimpleForm(request.POST)
        if not form.is_valid():

            context["summary_text"] = "Form is invalid"

            return render(request, get_app() / 'summary_present.html', context)
        else:
            from ..handlers.youtubelinkhandler import YouTubeLinkHandler

            youtube_link = form.cleaned_data['youtube_link']

            handler = YouTubeLinkHandler(youtube_link)
            handler.download_details()

            yt_json = handler.yt_ob.get_json()
            rd_json = handler.rd_ob.get_json()

            yt_props = str(yt_json)
            rd_props = str(rd_json)

            feed_url = handler.yt_ob.get_channel_feed_url()

            yt_props = [('webpage_url', yt_json['webpage_url'])]
            yt_props.append( ('title', yt_json['title']) )
            yt_props.append( ('uploader_url', yt_json['uploader_url']) )
            yt_props.append( ('channel_url', yt_json['channel_url']) )
            yt_props.append( ('channel_feed_url', feed_url) )
            yt_props.append( ('channel_id', yt_json['channel_id']) )

            for yt_prop in yt_json:
                yt_props.append( (yt_prop, str(yt_json[yt_prop])) )

            rd_props = []
            for rd_prop in rd_json:
                rd_props.append( (rd_prop, str(rd_json[rd_prop])) )

            context["youtube_props"] = yt_props
            context["return_dislike_props"] = rd_props

            context["yt_props"] = yt_props
            context["rd_props"] = rd_props

            return render(request, get_app() / 'show_youtube_link_props.html', context)


def write_bookmarks(request):
    context = get_context(request)
    context['page_title'] += " - Writer bookmarks"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    from ..datawriter import DataWriter
    
    c = Configuration.get_object(str(get_app()))
    writer = DataWriter(c)
    writer.write_bookmarks()

    context["summary_text"] = "Wrote OK"

    return render(request, get_app() / 'summary_present.html', context)


def write_yearly_data(request, year):
    context = get_context(request)
    context['page_title'] += " - Write yearly data"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    c = Configuration.get_object(str(get_app()))
    c.thread_mgr.write_yearly_data(year)

    context["summary_text"] = "Started writing yearly data"

    return render(request, get_app() / 'summary_present.html', context)


def write_topic(request, topic):
    context = get_context(request)
    context['page_title'] += " - tags writer"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    from ..serializers.bookmarksexporter import BookmarksTopicExporter

    c = Configuration.get_object(str(get_app()))
    exporter = BookmarksTopicExporter(c)
    exporter.export(topic)

    context["summary_text"] = "Wrote OK"

    return render(request, get_app() / 'summary_present.html', context)


def test_page(request):
    context = get_context(request)
    context['page_title'] += " - test page"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    summary_text = ""

    context["summary_text"] = summary_text

    return render(request, get_app() / 'summary_present.html', context)


def fix_bookmarked_yt(request):
    context = get_context(request)
    context['page_title'] += " - fix all"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    summary = ""
    links = LinkDataModel.objects.filter(persistent = True)
    for link in links:
        if fix_reset_youtube_link_details(link.id):
            summary += "Fixed: {} {}\n".format(link.link, link.title)
        else:
            summary += "Not Fixed: {} {}\n".format(link.link, link.title)

    context["summary_text"] = summary

    return render(request, get_app() / 'summary_present.html', context)


def user_config(request):
    context = get_context(request)
    context['page_title'] += " - User configuration"

    if not request.user.is_authenticated:
        return render(request, get_app() / 'missing_rights.html', context)

    user_name = request.user.get_username()
    
    ob = UserConfig.objects.filter(user = user_name)
    if not ob.exists():
        rec = UserConfig(user = user_name)
        rec.save()

    ob = UserConfig.objects.filter(user = user_name)

    if request.method == 'POST':
        form = UserConfigForm(request.POST, instance=ob[0])
        if form.is_valid():
            form.save()

        ob = UserConfig.objects.filter(user = user_name)
    
    form = UserConfigForm(request.POST, instance=ob[0])
    form.method = "POST"
    form.action_url = reverse('rsshistory:user-config')

    context['config_form'] = form

    return render(request, get_app() / 'user_configuration.html', context)


def clear_youtube_cache(request):
    context = get_context(request)
    context['page_title'] += " - clear youtube cache"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    from ..models import YouTubeMetaCache, YouTubeReturnDislikeMetaCache

    meta = YouTubeMetaCache.objects.all()
    meta.delete()

    dislike = YouTubeReturnDislikeMetaCache.objects.all()
    dislike.delete()

    summary = "Deleted all cache"
    context["summary_text"] = summary

    return render(request, get_app() / 'summary_present.html', context)
