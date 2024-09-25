from pathlib import Path
import traceback, sys
from datetime import timedelta
import datetime

from django.contrib.auth.models import User
from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import (
    UserTags,
    UserBookmarks,
    BaseLinkDataController,
    KeyWords,
    ConfigurationEntry,
)
from ..configuration import Configuration
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
    DomainsController,
    EntryWrapper,
)

from ..forms import (
    OmniSearchForm,
)
from ..views import ViewPage
from ..forms import LinkInputForm, OmniSearchForm
from ..pluginurl.urlhandler import UrlHandler


def test_page(request):
    p = ViewPage(request)
    p.set_title("Test page")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary_text = "test page"

    from ..controllers import EntriesCleanup

    entries = LinkDataController.objects.filter(title__icontains="slot server")
    entries.delete()

    # entries = LinkDataController.objects.filter(bookmarked=True)
    # for entry in entries:
    #    if not UserBookmarks.is_bookmarked(entry):
    #        UserBookmarks.add(request.user, entry)

    # start_date = datetime.date(2020, 1, 1)
    # stop_date = datetime.date(2025 + 1, 1, 1)

    # therange = (start_date, stop_date)

    # users = User.objects.filter(username=request.user)
    # if users.count() > 0:
    #    bookmarks = UserBookmarks.get_user_bookmarks(users[0])
    #    # this returns IDs, not 'objects'
    #    result_entries = bookmarks.values_list("entry_object", flat=True)
    #    result_entries = LinkDataController.objects.filter(id__in=result_entries)
    #    result_entries = result_entries.filter(date_published__range=therange)

    # summary_text = "Found bookmarked items = {}".format(result_entries.count())

    p.context["summary_text"] = summary_text

    return p.render("summary_present.html")


def test_form_page(request):
    p = ViewPage(request)
    p.set_title("Test form page")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary_text = ""

    form = OmniSearchForm(request.GET, request=request)
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
        for entry in entries:
            print("Fixing: {} {} {}".format(entry.link, entry.title, entry.source))
            h = UrlHandler(entry.link)
            h = h.p

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

        tags = UserTags.objects.all()
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
