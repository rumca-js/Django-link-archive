from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.db.models import Q

from collections import OrderedDict

from ..webtools import (
    ContentLinkParser,
    RssPage,
    DomainCache,
    DomainAwarePage,
    HttpPageHandler,
)

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    UserConfig,
    Browser,
    Gateway,
    EntryRules,
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
    LinkPropertiesForm,
)
from ..views import ViewPage
from ..pluginurl.urlhandler import UrlHandler


def get_errors(page_url):
    notes = []
    warnings = []
    errors = []

    link = page_url.url

    page = DomainAwarePage(link)
    config = Configuration.get_object().config_entry

    domain = page.get_domain()
    info = DomainCache.get_object(link, url_builder=UrlHandler)

    # warnings
    if config.prefer_https and link.find("http://") >= 0:
        warnings.append(
            "Detected http protocol. Choose https if possible. It is a more secure protocol"
        )
    if config.prefer_non_www_sites and domain.find("www.") >= 0:
        warnings.append(
            "Detected www in domain link name. Select non www link if possible"
        )
    if domain.lower() != domain:
        warnings.append("Link domain is not lowercase. Are you sure link name is OK?")
    if config.respect_robots_txt and info and not info.is_allowed(link):
        warnings.append("Link is not allowed by site robots.txt")
    if link.find("?") >= 0:
        warnings.append("Link contains arguments. Is that intentional?")
    if link.find("#") >= 0:
        warnings.append("Link contains arguments. Is that intentional?")
    if page.get_port() and page.get_port() >= 0:
        warnings.append("Link contains port. Is that intentional?")
    if not page.is_web_link():
        warnings.append(
            "Not a web link. Expecting protocol://domain.tld styled location"
        )

    response = page_url.get_response()

    # errors
    if not page.is_protocolled_link():
        errors.append("Not a protocolled link. Forget http:// or https:// etc.?")
    if not response:
        errors.append("Information about page availability could not be obtained")
    if response:
        code = response.get_status_code()
        if code < 200 or code > 300:
            errors.append("Invalid status code")
    if EntryRules.is_blocked(link):
        errors.append("Entry is blocked by entry rules")

    result = {}
    result["notes"] = notes
    result["warnings"] = warnings
    result["errors"] = errors

    return result


def get_page_properties(request):
    p = ViewPage(request)
    p.set_title("Page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data
        
    if "page" not in request.GET:
        data = {}
        data["status"] = False
        return JsonResponse(data, json_dumps_params={"indent":4})

    page_link = request.GET["page"]
    url = UrlHandler(page_link)
    options = url.get_init_page_options()

    browser = None

    if "browser" in request.GET and request.GET["browser"] != "":
        browsers = Browser.objects.filter(pk = request.GET["browser"])
        if browsers.exists():
            browser = browsers[0]
            options.bring_to_front(browser.get_setup())
            options.use_browser_promotions = False
        else:
            return

    if "html" in request.GET:
        page_url = UrlHandler(page_link, page_options=options, handler_class=HttpPageHandler)
    else:
        page_url = UrlHandler(page_link, page_options=options)
    response = page_url.get_response()

    page_handler = page_url.get_handler()

    is_link_allowed = DomainCache.get_object(page_link, url_builder=UrlHandler).is_allowed(page_link)

    all_properties = []

    properties = OrderedDict()
    properties["link"] = page_url.url
    properties["title"] = page_url.get_title()
    properties["description"] = page_url.get_description()
    properties["author"] = page_url.get_author()
    properties["album"] = page_url.get_album()
    properties["thumbnail"] = page_url.get_thumbnail()
    properties["language"] = page_url.get_language()
    properties["page_rating"] = page_url.get_page_rating()
    properties["date_published"] = page_url.get_date_published()
    properties["is_link_allowed"] = is_link_allowed

    feeds = page_url.get_feeds()
    if len(feeds) > 0:
        for key, feed in enumerate(feeds):
            properties["feed_"+str(key)] = feed

    if type(page_handler) is UrlHandler.youtube_channel_handler:
        if page_handler.get_channel_name():
            properties["channel_name"] = page_handler.get_channel_name()
            properties["channel_url"] = page_handler.get_channel_url()

    if type(page_handler) is UrlHandler.youtube_video_handler:
        if page_handler.get_channel_name():
            properties["channel_name"] = page_handler.get_channel_name()
            properties["channel_url"] = page_handler.get_channel_url()

    all_properties.append({"name" : "Properties", "data" : properties})

    all_properties.append({"name" : "Contents", "data" : {"Contents" : page_url.get_contents()}})

    request_data = OrderedDict()
    request_data["Options"] = str(page_url.options)
    if browser:
        request_data["Browser"] = str(browser.name)
        request_data["Browser Crawler"] = str(browser.crawler)
    request_data["Page Handler"] = str(page_handler.__class__.__name__)
    if hasattr(page_handler, "p"):
        request_data["Page Type"] = str(page_handler.p.__class__.__name__)

    all_properties.append({"name" : "Options", "data" : request_data})

    if response:
        response_data = OrderedDict()
        response_data["Response"] = str(response)
        response_data["status_code"] = response.get_status_code()
        response_data["Content-Type"] = response.get_content_type()
        response_data["Content-Length"] = response.get_content_length()
        all_properties.append({"name" : "Response", "data" : response_data})

    errors = get_errors(page_url)
    all_properties.append({"name" : "Errors", "data" : errors})

    data = OrderedDict()
    data["properties"] = all_properties
    data["status"] = True

    return JsonResponse(data, json_dumps_params={"indent":4})


def page_show_properties(request):
    p = ViewPage(request)
    p.set_title("Show page properties")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    form = LinkPropertiesForm(request=request)
    p.context["form"] = form
    return p.render("page_show_properties.html")


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
            p.context["summary_text"] = (
                "{} is allowed by <a href='{}'>robots.txt</a>".format(
                    url, c.get_robots_txt_url()
                )
            )
        else:
            p.context["summary_text"] = (
                "{} is NOT allowed by <a href='{}'>robots.txt</a>".format(
                    url, c.get_robots_txt_url()
                )
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

        return JsonResponse(data, json_dumps_params={"indent":4})

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

    Gateway.check_init()

    mapping = Gateway.get_types_mapping([Gateway.TYPE_SEARCH_ENGINE,
                                         Gateway.TYPE_AI_BOT,
                                         Gateway.TYPE_DIGITAL_LIBRARY])

    p.context["search_engines"] = mapping

    return p.render("search_engines.html")


def gateways(request):
    p = ViewPage(request)
    p.set_title("Gateways - useful places on the web")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    Gateway.check_init()

    mapping = Gateway.get_types_mapping([Gateway.TYPE_GATEWAY,
                                         Gateway.TYPE_APP_STORE,
                                         Gateway.TYPE_POPULAR,
                                         Gateway.TYPE_FAVOURITE,
                                         Gateway.TYPE_SOCIAL_MEDIA,
                                         Gateway.TYPE_AUDIO_STREAMING,
                                         Gateway.TYPE_VIDEO_STREAMING,
                                         Gateway.TYPE_FILE_SHARING,
                                         Gateway.TYPE_MARKETPLACE,
                                         Gateway.TYPE_OTHER,
                                         ])

    p.context["gateways"] = mapping

    return p.render("gateways.html")


def gateways_initialize(request):
    p = ViewPage(request)
    p.set_title("Gateways initialization")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data
    Gateway.objects.all().delete()
    Gateway.populate()

    p.context["summary_text"] = "Initialized gateways"
    return p.render("go_back.html")


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
        p.context["form_description_post"] = (
            "Internet is dangerous, so carefully select which links you add"
        )

        return p.render("form_oneliner.html")
