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
    LinkDataWrapper,
)
from ..views import ViewPage
from ..dateutils import DateUtils
from ..forms import LinkInputForm, ScannerForm, OmniSearchForm
from ..webtools import HtmlPage, ContentLinkParser, PageOptions
from ..pluginurl.urlhandler import UrlHandler


def page_show_properties(request):
    p = ViewPage(request)
    p.set_title("Show page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    def show_page_props_internal(requests, page_link):
        options = UrlHandler.get_url_options(page_link)
        options.fast_parsing = False

        page_handler = UrlHandler(page_link, page_options=options)
        ViewPage.fill_context_type(p.context, handler=page_handler.p)

        page_object = page_handler.p

        # fast check is disabled. We want to make sure based on contents if it is RSS or HTML
        p.context["page_object"] = page_object
        p.context["page_handler"] = page_handler
        p.context["response_object"] = page_handler.response
        p.context["page_object_type"] = str(type(page_object))

        return p.render("show_page_props.html")

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:page-show-props".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_basic.html")

        else:
            page_link = request.GET["page"]
            return show_page_props_internal(request, page_link)

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")
        else:
            page_link = form.cleaned_data["link"]
            return show_page_props_internal(request, page_link)


def create_scanner_form(request, links, additional_text=""):
    data = {}
    data["body"] = additional_text + "\n" + "\n".join(links)

    form = ScannerForm(initial=data, request=request)
    form.method = "POST"
    form.action_url = reverse("{}:page-add-many-links".format(LinkDatabase.name))
    return form


def page_scan_link(request):
    def render_page_scan_input(p, link):
        h = UrlHandler(link)
        contents = h.get_contents()
        parser = ContentLinkParser(link, contents)

        c = Configuration.get_object().config_entry

        links = []
        if c.auto_store_entries:
            links.extend(parser.get_links())
        if c.auto_store_domain_info:
            links.extend(parser.get_domains())

        links = set(links)
        if link in links:
            links.remove(link)

        links = list(links)
        links = sorted(links)

        p.context["form"] = create_scanner_form(request, links)
        p.context["form_submit_button_name"] = "Add links"
        return p.render("form_basic.html")

    p = ViewPage(request)
    p.set_title("Scans page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..forms import ExportDailyDataForm

    if request.method == "POST":
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            return p.render("form_basic.html")

        link = form.cleaned_data["link"]

        return render_page_scan_input(p, link)

    if request.method == "GET":
        if "link" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"

            p.context["form"] = form
            p.context["form_submit_button_name"] = "Scan"

            return p.render("form_basic.html")
        else:
            link = request.GET["link"]
            return render_page_scan_input(p, link)


def page_add_many_links(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    p = ViewPage(request)
    p.set_title("Scans page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = ScannerForm(request.POST, request=request)
        if form.is_valid():
            links = form.cleaned_data["body"]
            tag = form.cleaned_data["tag"]

            links = links.split("\n")
            for link in links:
                link = link.strip()
                link = link.replace("\r", "")

                if link != "":
                    BackgroundJobController.link_add(link, tag=tag, user=request.user)

        p.context["summary_text"] = "Added links"
        return p.render("summary_present.html")

    else:
        p.context["summary_text"] = "Error"

        return p.render("summary_present.html")


def page_scan_contents(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    p = ViewPage(request)
    p.set_title("Scans page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = ScannerForm(request.POST, request=request)
        if form.is_valid():
            contents = form.cleaned_data["body"]
            tag = form.cleaned_data["tag"]

            parser = ContentLinkParser(url="https://", contents=contents)
            links = sorted(list(parser.get_links()))

            form = create_scanner_form(request, links)
            p.context["form"] = form
            p.context["form_submit_button_name"] = "Add links"
            return p.render("form_basic.html")

        # form is invalid, it will display error
        return p.render("form_basic.html")

    else:
        form = ScannerForm(request=request)

        form.method = "POST"
        form.action_url = reverse("{}:page-scan-contents".format(LinkDatabase.name))
        p.context["form_submit_button_name"] = "Scan"
        p.context["form"] = form

        return p.render("form_basic.html")


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
        form = KeywordInputForm(request=request)
        form.method = "POST"
        form.action_url = reverse("{}:keyword-remove".format(LinkDatabase.name))
        p.context["form"] = form

        return p.render("form_basic.html")

    else:
        form = KeywordInputForm(request.POST, request=request)
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


def cleanup_link(request):
    from ..forms import LinkInputForm

    p = ViewPage(request)
    p.set_title("Cleanup Link")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = LinkInputForm(request.POST, request=request)
        if form.is_valid():
            link = form.cleaned_data["link"]

            link = UrlHandler.get_cleaned_link(link)

            summary_text = 'Cleaned up link: <a href="{}">{}</a>'.format(link, link)

            p.context["summary_text"] = summary_text

            return p.render("summary_present.html")
    else:
        form = LinkInputForm(request=request)
        form.method = "POST"

        p.context["form"] = form
        p.context[
            "form_description_post"
        ] = "Internet is dangerous, so carefully select which links you add"

        return p.render("form_basic.html")


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
