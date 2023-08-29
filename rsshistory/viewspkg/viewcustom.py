from pathlib import Path
import traceback, sys
from datetime import timedelta

from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..configuration import Configuration
from ..models import (
    LinkTagsDataModel,
)
from ..views import ContextData
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
)


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

            if not tag.link_obj.bookmarked:
                result.add(tag)
                break

        return list(result)

    def get_links_with_incorrect_language():
        from django.db.models import Q

        criterion1 = Q(language__contains="pl")
        criterion2 = Q(language__contains="en")
        criterion3 = Q(language__isnull=True)

        entries_no_object = LinkDataController.objects.filter(
            ~criterion1 & ~criterion2 & ~criterion3, bookmarked=True
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

            youtube_props = []
            youtube_props.append(("title", yt_json["title"]))
            youtube_props.append(("webpage_url", yt_json["webpage_url"]))
            youtube_props.append(("uploader_url", yt_json["uploader_url"]))
            youtube_props.append(("channel_id", yt_json["channel_id"]))
            youtube_props.append(("channel", yt_json["channel"]))
            youtube_props.append(("channel_url", yt_json["channel_url"]))
            youtube_props.append(("channel_feed_url", feed_url))
            youtube_props.append(
                ("channel_follower_count", yt_json["channel_follower_count"])
            )
            youtube_props.append(("view_count", yt_json["view_count"]))
            youtube_props.append(("like_count", yt_json["like_count"]))
            youtube_props.append(("language", yt_json["language"]))
            youtube_props.append(("upload_date", yt_json["upload_date"]))
            youtube_props.append(("duration", yt_json["duration_string"]))

            all_youtube_props = []
            for yt_prop in yt_json:
                all_youtube_props.append((yt_prop, str(yt_json[yt_prop])))

            rd_props = []
            for rd_prop in rd_json:
                rd_props.append((rd_prop, str(rd_json[rd_prop])))

            context["youtube_props"] = youtube_props
            context["return_dislike_props"] = rd_props
            context["all_youtube_props"] = all_youtube_props

            return ContextData.render(request, "show_youtube_link_props.html", context)


def test_page(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - test page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    summary_text = ""

    from ..threadhandlers import ImportSourcesJobHandler

    handler = ImportSourcesJobHandler()
    handler.process()

    # LinkDataController.move_old_links_to_archive()

    # items = LinkDataController.objects.filter(source="https://pluralistic.net/feed")
    # items.delete()

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
    links = LinkDataController.objects.filter(bookmarked=True)
    for link in links:
        if fix_reset_youtube_link_details(link.id):
            summary += "Fixed: {} {}\n".format(link.link, link.title)
        else:
            summary += "Not Fixed: {} {}\n".format(link.link, link.title)

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


def check_if_move_to_archive(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Move to archive"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    LinkDataController.move_all_to_archive()

    context["summary_text"] = "Moved links to archive"

    return ContextData.render(request, "summary_present.html", context)
