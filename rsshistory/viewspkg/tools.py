from django.urls import reverse

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
)
from ..controllers import (
    EntryDataBuilder,
    BackgroundJobController,
)
from ..configuration import Configuration
from ..forms import (
    LinkInputForm,
    ScannerForm,
    UrlContentsForm,
)
from ..views import ViewPage
from ..pluginurl.urlhandler import UrlHandler
from ..webtools import ContentLinkParser, RssPage, DomainCache


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
        p.context["is_link_allowed"] = DomainCache.get_object(page_link).is_allowed(page_link)

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


def create_scanner_form(request, links):
    data = {}
    data["body"] = "\n".join(links)

    form = ScannerForm(initial=data, request=request)
    form.method = "POST"
    form.action_url = reverse("{}:page-add-many-links".format(LinkDatabase.name))
    return form


def get_scan_contents_links(link, contents):
    parser = ContentLinkParser(link, contents)

    c = Configuration.get_object().config_entry

    links = []
    if c.accept_not_domain_entries:
        links.extend(parser.get_links())
    if c.accept_domains:
        links.extend(parser.get_domains())

    links = set(links)
    if link in links:
        links.remove(link)

    links = list(links)
    links = sorted(links)

    return links


def page_scan_link(request):
    def render_page_scan_input(p, link):
        h = UrlHandler(link)
        contents = h.get_contents()

        links = get_scan_contents_links(link, contents)

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

            link = "https://"  # TODO this might not work for some URLs
            links = get_scan_contents_links(link, contents)

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


def page_process_contents(request):
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
        form = UrlContentsForm(request.POST, request=request)
        if form.is_valid():
            contents = form.cleaned_data["body"]
            link = form.cleaned_data["url"]

            # TODO should this be more connected with source processing?
            # IT should not be just RssPage, but also HtmlPage, or other handlers
            reader = RssPage(link, contents=contents)
            if not reader.is_valid():
                p.context["summary_text"] = "Contents is invalid"
                return p.render("summary_present.html")

            summary = "Added: "

            summary += "<ul>"

            all_props = reader.get_container_elements()
            for index, prop in enumerate(all_props):
                prop["link"] = UrlHandler.get_cleaned_link(prop["link"])
                # TODO use language from source, if we have source for that url/link
                # TODO update page hash?

                b = EntryDataBuilder()
                b.link_data = prop
                b.source_is_auto = True
                entry = b.add_from_props()

                if entry:
                    summary += "<li><a href='{}'>{}:{}</a></li>".format(
                        entry.get_absolute_url(), prop["link"], prop["title"]
                    )

            summary += "</ul>"

            p.context["summary_text"] = summary
            return p.render("summary_present.html")

        # form is invalid, it will display error
        return p.render("form_basic.html")

    else:
        form = UrlContentsForm(request=request)

        form.method = "POST"
        form.action_url = reverse("{}:page-process-contents".format(LinkDatabase.name))
        p.context["form_submit_button_name"] = "Process"
        p.context["form"] = form

        return p.render("form_basic.html")


def download_url(request):
    p = ViewPage(request)
    p.set_title("Download url")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:download-video-url".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_basic.html")

        else:
            url = request.GET["page"]

            BackgroundJobController.download_file(url)

            p.context["summary_text"] = "Added to download queue"
            return p.render("summary_present.html")

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        BackgroundJobController.download_file(url)

        p.context["summary_text"] = "Added to download queue"
        return p.render("summary_present.html")


def download_music(request):
    p = ViewPage(request)
    p.set_title("Download music")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:download-music-url".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_basic.html")

        else:
            url = request.GET["page"]

            BackgroundJobController.download_music_url(url)

            p.context["summary_text"] = "Added to download queue"
            return p.render("summary_present.html")

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        BackgroundJobController.download_music_url(url)

        p.context["summary_text"] = "Added to download queue"
        return p.render("summary_present.html")


def download_video(request):
    p = ViewPage(request)
    p.set_title("Download video")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:download-video-url".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_basic.html")

        else:
            url = request.GET["page"]

            BackgroundJobController.download_video_url(url)

            p.context["summary_text"] = "Added to download queue"
            return p.render("summary_present.html")

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        BackgroundJobController.download_video_url(url)

        p.context["summary_text"] = "Added to download queue"
        return p.render("summary_present.html")


def is_url_allowed(request):
    p = ViewPage(request)
    p.set_title("Is link allowed by robots.txt")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:is-url-allowed".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_basic.html")

        else:
            url = request.GET["page"]

            c = DomainCache.get_object(url)
            status = c.is_allowed(url)

            if status:
                p.context["summary_text"] = "{} is allowed by <a href='{}'>robots.txt</a>".format(url, c.get_robots_txt_url())
            else:
                p.context["summary_text"] = "{} is NOT allowed by <a href='{}'>robots.txt</a>".format(url, c.get_robots_txt_url())
            return p.render("summary_present.html")

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        c = DomainCache.get_object(url)
        status = c.is_allowed(url)

        if status:
            p.context["summary_text"] = "{} is allowed by <a href='{}'>robots.txt</a>".format(url, c.get_robots_txt_url())
        else:
            p.context["summary_text"] = "{} is NOT allowed by <a href='{}'>robots.txt</a>".format(url, c.get_robots_txt_url())
        return p.render("summary_present.html")
