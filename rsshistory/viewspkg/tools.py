from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import redirect

from ..webtools import ContentLinkParser, RssPage, DomainCache, DomainAwarePage

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    BrowserMode,
    UserConfig,
)
from ..controllers import (
    LinkDataController,
    EntryDataBuilder,
    BackgroundJobController,
    SearchEngines,
)
from ..configuration import Configuration
from ..forms import (
    LinkInputForm,
    ScannerForm,
    UrlContentsForm,
)
from ..views import ViewPage
from ..pluginurl.urlhandler import UrlHandler


def page_show_properties(request):
    p = ViewPage(request)
    p.set_title("Show page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    def show_page_props_internal(requests, page_link):
        url = UrlHandler(page_link)
        options = url.options

        method = "standard"

        if "method" in request.GET and request.GET["method"] != "":
            options.mode = request.GET["method"]
        else:
            options.use_browser_promotions = True

        page_url = UrlHandler(page_link, page_options=options)
        page_url.get_response()

        ViewPage.fill_context_type(p.context, urlhandler=page_url)

        page_handler = page_url.get_handler()

        # fast check is disabled. We want to make sure based on contents if it is RSS or HTML
        p.context["page_url"] = page_url
        p.context["page_handler"] = page_handler
        p.context["page_handler_type"] = str(type(page_handler))
        p.context["is_link_allowed"] = DomainCache.get_object(
            page_link, url_builder=UrlHandler
        ).is_allowed(page_link)
        p.context["method"] = options.mode
        p.context["modes"] = BrowserMode.get_modes()

        return p.render("show_page_props.html")

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:page-show-props".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_oneliner.html")

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
    def render_page_scan_input(p, link, template="form_basic.html"):
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
            return render_page_scan_input(p, link, "form_oneliner.html")


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
        return p.render("go_back.html")

    else:
        p.context["summary_text"] = "Error"

        return p.render("go_back.html")


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


def page_process_rss_contents(request):
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

            all_props = reader.get_entries()
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
    def download_url_internal(p, url):
        BackgroundJobController.download_file(url, user=request.user)

        p.context["summary_text"] = "Added to download queue"
        return p.render("go_back.html")

    p = ViewPage(request)
    p.set_title("Download url")

    uc = UserConfig.get(request.user)
    if not uc.can_download():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    p.context["form_submit_button_name"] = "Download"

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:download-video-url".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_oneliner.html")

        else:
            url = request.GET["page"]

            return download_url_internal(p, url)

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        return download_url_internal(p, url)


def download_music(request):
    def download_music_internal(p, url):
        BackgroundJobController.download_music_url(url, user=request.user)

        p.context["summary_text"] = "Added to download queue"
        return p.render("go_back.html")

    p = ViewPage(request)
    p.set_title("Download music")

    uc = UserConfig.get(request.user)
    if not uc.can_download():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    p.context["form_submit_button_name"] = "Download"

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:download-music-url".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_oneliner.html")

        else:
            url = request.GET["page"]

            return download_music_internal(p, url)

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        return download_music_internal(p, url)


def download_video(request):
    def download_video_internal(p, url):
        BackgroundJobController.download_video_url(url, user=request.user)

        p.context["summary_text"] = "Added to download queue"
        return p.render("go_back.html")

    p = ViewPage(request)
    p.set_title("Download video")

    uc = UserConfig.get(request.user)
    if not uc.can_download():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    p.context["form_submit_button_name"] = "Download"

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:download-video-url".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_oneliner.html")

        else:
            url = request.GET["page"]

            return download_video_internal(p, url)

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]
        return download_video_internal(p, url)


def download_music_pk(request, pk):
    p = ViewPage(request)
    p.set_title("Download music")

    uc = UserConfig.get(request.user)
    if not uc.can_download():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    p.context["form_submit_button_name"] = "Download"

    ft = LinkDataController.objects.filter(id=pk)
    if ft.exists():
        p.context["summary_text"] = "Added to download queue"
    else:
        p.context["summary_text"] = "Failed to add to download queue"

    BackgroundJobController.download_music(ft[0], user=request.user)

    return p.render("go_back.html")


def download_video_pk(request, pk):
    p = ViewPage(request)
    p.set_title("Download video")

    uc = UserConfig.get(request.user)
    if not uc.can_download():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    p.context["form_submit_button_name"] = "Download"

    ft = LinkDataController.objects.filter(id=pk)
    if ft.exists():
        p.context["summary_text"] = "Added to download queue"
    else:
        p.context["summary_text"] = "Failed to add to download queue"

    BackgroundJobController.download_video(ft[0], user=request.user)

    return p.render("go_back.html")


def is_url_allowed(request):
    def is_url_allowed_internal(p, url):
        c = DomainCache.get_object(url, url_builder=UrlHandler)
        status = c.is_allowed(url)

        if status:
            p.context[
                "summary_text"
            ] = "{} is allowed by <a href='{}'>robots.txt</a>".format(
                url, c.get_robots_txt_url()
            )
        else:
            p.context[
                "summary_text"
            ] = "{} is NOT allowed by <a href='{}'>robots.txt</a>".format(
                url, c.get_robots_txt_url()
            )
        return p.render("summary_present.html")

    p = ViewPage(request)
    p.set_title("Is link allowed by robots.txt")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:is-url-allowed".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_oneliner.html")

        else:
            url = request.GET["page"]

            return is_url_allowed_internal(p, url)

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        return is_url_allowed_internal(p, url)


def page_verify(request):
    def page_verify_internal(url):
        entries = LinkDataController.objects.filter(link=url)
        data = {}

        if entries.exists():
            entry = entries[0]
            data["entry"] = entry.get_map()
        else:
            c = Configuration.get_object().config_entry
            if c.auto_scan_entries:
                BackgroundJobController.link_add(url)

        domain_url = DomainAwarePage(url).get_domain()
        if domain_url != url:
            domains = LinkDataController.objects.filter(link=domain_url)
            if domains.exists():
                domain = domains[0]
                data["domain"] = domain.get_map()

        return JsonResponse(data)

    p = ViewPage(request)
    p.set_title("Verify page")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["form_submit_button_name"] = "Verify"

    if request.method == "GET":
        if "page" not in request.GET:
            form = LinkInputForm(request=request)
            form.method = "POST"
            form.action_url = reverse("{}:page-verify".format(LinkDatabase.name))
            p.context["form"] = form

            return p.render("form_oneliner.html")

        else:
            url = request.GET["page"]

            return page_verify_internal(url)

    else:
        form = LinkInputForm(request.POST, request=request)
        if not form.is_valid():
            p.context["summary_text"] = "Form is invalid"

            return p.render("summary_present.html")

        url = form.cleaned_data["link"]

        return page_verify_internal(url)


def search_engines(request):
    p = ViewPage(request)
    p.set_title("Search engines")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    search_engines = []
    ai_search_engines = []
    archives = []

    engine_classes = SearchEngines.get_search_engines()
    for engine_class in engine_classes:
        engine = engine_class()
        search_engines.append(engine)

    engine_classes = SearchEngines.get_aibots()
    for engine_class in engine_classes:
        engine = engine_class()
        ai_search_engines.append(engine)

    engine_classes = SearchEngines.get_archive_libraries()
    for engine_class in engine_classes:
        engine = engine_class()
        archives.append(engine)

    p.context["search_engines"] = search_engines
    p.context["ai_search_engines"] = ai_search_engines
    p.context["archives"] = archives

    return p.render("search_engines.html")


def gateways(request):
    p = ViewPage(request)
    p.set_title("Gateways - useful places on the web")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    result = []

    engine_classes = SearchEngines.get_gateways()
    for engine_class in engine_classes:
        engine = engine_class()
        result.append(engine)

    p.context["gateways"] = result

    return p.render("gateways.html")


def cleanup_link(request):
    p = ViewPage(request)
    p.set_title("Cleanup Link")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
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

        return p.render("form_oneliner.html")
