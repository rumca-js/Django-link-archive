from pathlib import Path
import traceback, sys
from datetime import timedelta

from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..apps import LinkDatabase
from ..models import (
    LinkTagsDataModel,
    BaseLinkDataController,
    KeyWords,
)
from ..configuration import ConfigurationEntry
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
)
from ..views import ViewPage
from ..dateutils import DateUtils
from ..forms import LinkInputForm


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

    p = ViewPage(request)
    p.set_title("Data errors")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    # fix_reassign_source_to_nullsource_entries()
    # fix_tags_links()

    summary_text = "Done"
    try:
        p.context["links_with_incorrect_language"] = get_links_with_incorrect_language()
        p.context["incorrect_youtube_links"] = get_incorrect_youtube_links()
        p.context["tags_for_missing_links"] = get_tags_for_missing_links()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)

    # find links without source

    # remove tags, for which we do not have links, or entry is not bookmarked

    # show bookmarked links without tags

    return p.render("data_errors.html")


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
    if sources_obj.count() > 0:
        source_obj = sources_obj[0]

    entry.title = h.get_title()
    entry.description = h.get_description()[
        : BaseLinkDataController.get_description_length() - 2
    ]
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

    p = ViewPage(request)
    p.set_title("Fix YouTube links")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary_text = ""
    if fix_reset_youtube_link_details(pk):
        summary_text += "Fixed {}".format(pk)
    else:
        summary_text += "Not fixed {}".format(pk)

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def fix_entry_tags(request, entrypk):
    p = ViewPage(request)
    p.set_title("Fix entry tags")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=entrypk)
    tags = entry.tags.all()

    summary_text = ""
    for tag in tags:
        tag.link = tag.link_obj.link
        tag.save()
        summary_text += "Fixed: {}".format(tag.id)

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def show_youtube_link_props(request):
    p = ViewPage(request)
    p.set_title("Show YouTube link properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..forms import YouTubeLinkSimpleForm

    youtube_link = "https:"
    if not request.method == "POST":
        form = YouTubeLinkSimpleForm(initial={"youtube_link": youtube_link})
        form.method = "POST"
        form.action_url = reverse(
            "{}:show-youtube-link-props".format(LinkDatabase.name)
        )
        p.context["form"] = form

        return p.render("form_basic.html")

    else:
        form = YouTubeLinkSimpleForm(request.POST)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")
        else:
            from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

            youtube_link = form.cleaned_data["youtube_link"]

            handler = YouTubeLinkHandler(youtube_link)
            handler.download_details()

            yt_json = handler.yt_ob.get_json()
            # TODO rd_json = handler.rd_ob.get_json()

            yt_props = str(yt_json)
            # TODO rd_props = str(rd_json)

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
            if "language" in yt_json:
                youtube_props.append(("language", yt_json["language"]))
            youtube_props.append(("upload_date", yt_json["upload_date"]))
            if "duration_string" in yt_json:
                youtube_props.append(("duration", yt_json["duration_string"]))
            youtube_props.append(("valid", handler.is_valid()))

            all_youtube_props = []
            for yt_prop in yt_json:
                all_youtube_props.append((yt_prop, str(yt_json[yt_prop])))

            # rd_props = []
            # for rd_prop in rd_json:
            #    rd_props.append((rd_prop, str(rd_json[rd_prop])))

            p.context["youtube_props"] = youtube_props
            # p.context["return_dislike_props"] = rd_props
            p.context["all_youtube_props"] = all_youtube_props

            return p.render("show_youtube_link_props.html")


def show_page_props(request):
    p = ViewPage(request)
    p.set_title("Show page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..webtools import Page

    if not request.method == "POST":
        form = LinkInputForm()
        form.method = "POST"
        form.action_url = reverse("{}:show-page-props".format(LinkDatabase.name))
        p.context["form"] = form

        return p.render("form_basic.html")

    else:
        form = LinkInputForm(request.POST)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")
        else:
            from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

            page_link = form.cleaned_data["link"]

            page = Page(page_link)

            p.context["show_properties"] = page.get_properties()

            return p.render("show_properties.html")


def test_page(request):
    p = ViewPage(request)
    p.set_title("Test page")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary_text = "test page"

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def test_form_page(request):
    from ..forms import OmniSearchForm

    p = ViewPage(request)
    p.set_title("Test form page")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary_text = ""

    form = OmniSearchForm(request.GET)
    p.context["form"] = form

    return p.render("form_basic.html")


def fix_bookmarked_yt(request):
    p = ViewPage(request)
    p.set_title("Fix bookmarked entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary = ""
    links = LinkDataController.objects.filter(bookmarked=True)
    for link in links:
        if fix_reset_youtube_link_details(link.id):
            summary += "Fixed: {} {}\n".format(link.link, link.title)
        else:
            summary += "Not Fixed: {} {}\n".format(link.link, link.title)

    p.context["summary_text"] = summary

    return p.render("summary_present.html")


def download_music(request, pk):
    p = ViewPage(request)
    p.set_title("Download music")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ft = LinkDataController.objects.filter(id=pk)
    if ft.exists():
        p.context["summary_text"] = "Added to download queue"
    else:
        p.context["summary_text"] = "Failed to add to download queue"

    BackgroundJobController.download_music(ft[0])

    return p.render("summary_present.html")


def download_video(request, pk):
    p = ViewPage(request)
    p.set_title("Download video")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ft = LinkDataController.objects.filter(id=pk)
    if ft.exists():
        p.context["summary_text"] = "Added to download queue"
    else:
        p.context["summary_text"] = "Failed to add to download queue"

    BackgroundJobController.download_video(ft[0])

    return p.render("summary_present.html")


def check_if_move_to_archive(request):
    p = ViewPage(request)
    p.set_title("Move to archive")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    LinkDataController.move_all_to_archive()

    p.context["summary_text"] = "Moved links to archive"

    return p.render("summary_present.html")


def show_info(request):
    p = ViewPage(request)

    info = "Cannot make query"
    p.set_title("Info: {}".format(info))

    p.context["summary_text"] = info

    return p.render("summary_present.html")


def keywords(request):
    p = ViewPage(request)
    p.set_title("Keywords")

    content_list = KeyWords.get_keyword_data()
    if len(content_list) >= 0:
        p.context["content_list"] = content_list

    objects = KeyWords.objects.all()
    if len(objects) > 0:
        min_val = objects[0].date_published
        for aobject in KeyWords.objects.all():
            if min_val > aobject.date_published:
                min_val = aobject.date_published
        p.context["last_date"] = min_val

    return p.render("keywords_list.html")


def keywords_remove_all(request):
    p = ViewPage(request)
    p.set_title("Keywords remove all")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    keys = KeyWords.objects.all()
    keys.delete()

    return redirect("{}:keywords".format(LinkDatabase.name))


def keyword_remove(request):
    p = ViewPage(request)
    p.set_title("Remove a keyword")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..forms import KeywordInputForm

    if not request.method == "POST":
        form = KeywordInputForm()
        form.method = "POST"
        form.action_url = reverse("{}:keyword-remove".format(LinkDatabase.name))
        p.context["form"] = form

        return p.render("form_basic.html")

    else:
        form = KeywordInputForm(request.POST)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")
        else:
            keyword = form.cleaned_data["keyword"]
            keywords = KeyWords.objects.filter(keyword=keyword)
            keywords.delete()

            return HttpResponseRedirect(
                reverse("{}:keywords".format(LinkDatabase.name))
            )
