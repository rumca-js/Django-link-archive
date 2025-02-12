from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.db.models import Q

from collections import OrderedDict

from ..webtools import (
    ContentLinkParser,
    RssPage,
    UrlLocation,
    HttpPageHandler,
    RemoteServer,
)

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    UserConfig,
    Browser,
    Gateway,
    EntryRules,
    AppLogging,
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
from ..pluginurl.urlhandler import UrlHandlerEx


def get_errors(page_url):
    notes = []
    warnings = []
    errors = []

    link = page_url.url

    page = UrlLocation(link)
    config = Configuration.get_object().config_entry

    domain = page.get_domain()
    u = UrlHandlerEx(link)
    is_allowed = u.is_allowed()

    # warnings
    if config.prefer_https_links and link.find("http://") >= 0:
        warnings.append(
            "Detected http protocol. Choose https if possible. It is a more secure protocol"
        )
    if config.prefer_non_www_links and domain.find("www.") >= 0:
        warnings.append(
            "Detected www in domain link name. Select non www link if possible"
        )
    if domain.lower() != domain:
        warnings.append("Link domain is not lowercase. Are you sure link name is OK?")
    if config.respect_robots_txt and not is_allowed:
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
        return JsonResponse(data, json_dumps_params={"indent": 4})

    page_link = request.GET["page"]

    browser = None

    if "browser" in request.GET and request.GET["browser"] != "":
        browser_pk = int(request.GET["browser"])

        if browser_pk != Browser.AUTO:
            browsers = Browser.objects.filter(pk=browser_pk)
            if browsers.exists():
                browser = browsers[0]
            else:
                AppLogging.error("Browser does not exist!")
                return

    settings = {}
    if "html" in request.GET:
        settings["handler_class"] = "HttpPageHandler"

    if browser:
        browsers = [browser.get_setup()]
    else:
        browsers = None

    url_ex = UrlHandlerEx(page_link, settings=settings, browsers=browsers)
    all_properties = url_ex.get_properties()

    # TODO remove hardcoded value
    if len(all_properties) > 3:
        if "data" in all_properties[3]:
            if "hash" in all_properties[3]["data"]:
                all_properties[3]["data"]["body_hash"] = str(all_properties[3]["data"]["body_hash"])
                all_properties[3]["data"]["hash"] = str(all_properties[3]["data"]["hash"])

    data = OrderedDict()
    data["properties"] = all_properties
    data["status"] = True

    return JsonResponse(data, json_dumps_params={"indent": 4})


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
    if c.accept_non_domain_links:
        links.extend(parser.get_links())
    if c.accept_domain_links:
        links.extend(parser.get_domains())

    links = set(links)
    if link in links:
        links.remove(link)

    links = list(links)
    links = sorted(links)

    return links


def page_scan_link(request):
    def render_page_scan_input(p, link, template="form_basic.html"):
        h = UrlHandlerEx(link)
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
        u = UrlHandlerEx(url)
        status = u.is_allowed()

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
            if c.auto_scan_new_entries:
                BackgroundJobController.link_add(url)

        domain_url = UrlLocation(url).get_domain()
        if domain_url != url:
            domains = LinkDataController.objects.filter(link=domain_url)
            if domains.exists():
                domain = domains[0]
                data["domain"] = domain.get_map()

        return JsonResponse(data, json_dumps_params={"indent": 4})

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

    mapping = Gateway.get_types_mapping(
        [Gateway.TYPE_SEARCH_ENGINE, Gateway.TYPE_AI_BOT, Gateway.TYPE_DIGITAL_LIBRARY]
    )

    p.context["search_engines"] = mapping

    return p.render("search_engines.html")


def gateways(request):
    p = ViewPage(request)
    p.set_title("Gateways - useful places on the web")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    Gateway.check_init()

    mapping = Gateway.get_types_mapping(
        [
            Gateway.TYPE_GATEWAY,
            Gateway.TYPE_APP_STORE,
            Gateway.TYPE_POPULAR,
            Gateway.TYPE_FAVOURITE,
            Gateway.TYPE_SOCIAL_MEDIA,
            Gateway.TYPE_AUDIO_STREAMING,
            Gateway.TYPE_VIDEO_STREAMING,
            Gateway.TYPE_FILE_SHARING,
            Gateway.TYPE_MARKETPLACE,
            Gateway.TYPE_BANKING,
            Gateway.TYPE_OTHER,
        ]
    )

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

            link = UrlHandlerEx.get_cleaned_link(link)

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
