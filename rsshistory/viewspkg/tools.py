"""
Some say "programming is a convesation". Maybe it is true.
In that case it looks as if one was totally drunk.
"""

from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.db.models import Q

from collections import OrderedDict

from webtoolkit import (
    UrlLocation,
    ContentLinkParser,
    RemoteUrl,
    is_status_code_invalid,
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
    SystemOperationController,
)
from ..configuration import Configuration
from ..forms import (
    LinkInputForm,
    ScannerForm,
    UrlContentsForm,
    LinkPropertiesForm,
)
from ..views import (
    ViewPage,
    SimpleViewPage,
    get_request_browser,
    get_request_url_with_browser,
)
from ..pluginurl.urlhandler import UrlHandler


def get_errors(page_url):
    notes = []
    warnings = []
    errors = []

    link = page_url.url

    location = UrlLocation(link)
    config = Configuration.get_object().config_entry

    domain = location.get_domain()
    u = UrlHandler(link)
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
    if not is_allowed:
        warnings.append("Link is not allowed by site robots.txt")
    if link.find("?") >= 0:
        warnings.append("Link contains arguments. Is that intentional?")
    if link.find("#") >= 0:
        warnings.append("Link contains arguments. Is that intentional?")
    if location.get_port() and location.get_port() >= 0:
        warnings.append("Link contains port. Is that intentional?")
    if not location.is_web_link():
        warnings.append(
            "Not a web link. Expecting protocol://domain.tld styled location"
        )

    response = page_url.get_response()

    # errors
    if not location.is_protocolled_link():
        errors.append("Not a protocolled link. Forget http:// or https:// etc.?")
    if not response:
        errors.append("Information about page availability could not be obtained")
    if response:
        code = response.get_status_code()
        if is_status_code_invalid(code):
            errors.append("Invalid status code")

    if page_url.is_blocked():
        reason = page_url.get_block_reason()
        errors.append(
            "Web page is blocked. Check entry rules, configuration. Reason:{}".format(
                reason
            )
        )

    result = {}
    result["notes"] = notes
    result["warnings"] = warnings
    result["errors"] = errors

    return result


def json_page_properties(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    if "link" not in request.GET:
        data = {}
        data["status"] = False
        data["errors"] = ["Link in not in arguments"]
        return JsonResponse(data, json_dumps_params={"indent": 4})

    system = SystemOperationController()
    if system.is_remote_server_down():
        data = {}
        data["status"] = False
        data["errors"] = ["Crawling server is down"]
        return JsonResponse(data, json_dumps_params={"indent": 4})

    url_ex = get_request_url_with_browser(request.GET)
    all_properties = url_ex.get_properties()

    if not all_properties:
        data = OrderedDict()
        data["properties"] = all_properties
        data["status"] = False
        data["errors"] = ["Could not obtain properties"]
        return JsonResponse(data, json_dumps_params={"indent": 4})

    for item in all_properties:
        if item["name"] == "Response":
            if "data" in item:
                if "hash" in item["data"]:
                    item["data"]["body_hash"] = str(item["data"]["body_hash"])
                    item["data"]["hash"] = str(item["data"]["hash"])

    data = OrderedDict()
    data["properties"] = all_properties
    data["status"] = True

    page_link = request.GET["link"]
    things = get_errors(url_ex)
    if things:
        data["errors"] = things["errors"]
        data["warnings"] = things["warnings"]
        data["notes"] = things["notes"]

    return JsonResponse(data, json_dumps_params={"indent": 4})


def page_show_props(request):
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
    def render_page_scan_input(url, link, template="form_basic.html"):
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
        form = LinkPropertiesForm(request.POST, request=request)
        if not form.is_valid():
            return p.render("form_basic.html")

        link = form.cleaned_data["link"]
        url = get_request_url_with_browser(form.cleaned_data)

        return render_page_scan_input(url, link)

    if request.method == "GET":
        if "link" not in request.GET:
            form = LinkPropertiesForm(request=request)
            form.method = "POST"

            p.context["form"] = form
            p.context["form_submit_button_name"] = "Scan"

            return p.render("form_basic.html")
        else:
            link = request.GET["link"]
            url = get_request_url_with_browser(request.GET)
            return render_page_scan_input(url, link, "form_oneliner.html")


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
        # TODO use Remote?
        u = UrlHandler(url)
        u.get_response()
        status = u.is_allowed()

        if status:
            p.context["summary_text"] = (
                "{} is allowed by robots.txt".format(
                    url
                )
            )
        else:
            p.context["summary_text"] = (
                "{} is NOT allowed by robots.txt".format(
                    url
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

    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

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


def searchviews_initialize(request):
    p = ViewPage(request)
    p.set_title("Searchviews initialization")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    views = SearchView.objects.all()
    views.delete()

    SearchView.objects.create(name="Default", order_by="-page_rating, link")
    SearchView.objects.create(
        name="Votes", order_by="-page_rating_votes, -page_rating, link"
    )
    SearchView.objects.create(name="What's published", order_by="-date_published")
    SearchView.objects.create(name="What's created", order_by="-date_created")
    SearchView.objects.create(
        name="Bookmarked",
        filter_statement="bookmarked=True",
        order_by="-date_created",
        user=True,
    )

    p.context["summary_text"] = "Initialized searchviews"
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


def cleanup_link_json(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    data = {}
    links = set()

    if "link" in request.GET:
        original_link = request.GET["link"]
        cleaned_link = UrlHandler.get_cleaned_link(original_link)

        links.add(cleaned_link)

        links -= {original_link}

        data["links"] = sorted(links)
        data["status"] = True
    else:
        data["status"] = False

    return JsonResponse(data, json_dumps_params={"indent": 4})

def get_suggestions(original_link):
    data = {}
    links = set()
    errors = []

    cleaned_link = UrlHandler.get_cleaned_link(original_link)

    location = UrlLocation(original_link)

    links.add(cleaned_link)

    config = Configuration.get_object().config_entry
    if config.accept_domain_links:
        links.add(location.get_domain())

    if original_link.endswith("/"):
        errors.append("Link should not end with slash")

    if not config.accept_domain_links and location.is_domain():
        errors.append(
            "This is domain link, and system is configured not to accept that"
        )

    if not config.accept_non_domain_links and not location.is_domain():
        errors.append(
            "This is not a domain link, and system is configured not to accept that"
        )

    if config.prefer_non_www_links and original_link.find("www") >= 0:
        errors.append("This link has www inside")

    if config.prefer_https_links and original_link.find("http://") >= 0:
        errors.append("This link has http inside, prefer https")

    if original_link.find("http://") >= 0:
        links.add(location.get_protocol_url("https"))

    if original_link.find("www.") >= 0:
        link = original_link.replace("www.", "")
        links.add(link)

    links.discard(None)
    links -= {original_link}

    data["links"] = sorted(links)
    data["errors"] = errors
    data["status"] = True

    return data


def link_input_suggestions_json(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    if "link" in request.GET:
        data = get_suggestions(request.GET["link"])

    return JsonResponse(data, json_dumps_params={"indent": 4})


def source_input_suggestions_json(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    if "link" in request.GET:
        link = request.GET["link"]
        data = get_suggestions(link)
        url = RemoteUrl(link)
        feeds = url.get_feeds()
        for feed in feeds:
            if feed not in data["links"] and feed != link:
                data["links"].append(feed)

    return JsonResponse(data, json_dumps_params={"indent": 4})


# TODO Gmail things below.
"""
Steps to enable:
 - create a project
 - enabled gmail API (API & Services -> library), enable
 - configure OAuth consent screen
    - choose external
    - add scope https://www.googleapis.com/auth/gmail.readonly
 - create OAuth 2.0 credentials
    - APIs & Services -> Credentials
    - create credentials -> OAuth client ID
    - choose web application
    - set authorized redirect URL
 - you will receive YOUR_CLIENT_ID and YOUR_CLIENT_SECRET
"""


def gmail_auth(request):
    client_id = "YOUR_CLIENT_ID"

    config = Configuration.get_object().config_entry
    location = config.instance_internet_location

    redirect_uri = f"{location}/oauth2callback/"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return redirect(url)


def oauth2callback(request):
    code = request.GET.get("code")

    client_id = "YOUR_CLIENT_ID"
    client_secret = "YOUR_CLIENT_SECRET"

    config = Configuration.get_object().config_entry
    location = config.instance_internet_location

    redirect_uri = f"{location}/oauth2callback/"

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    response = requests.post("https://oauth2.googleapis.com/token", data=data)
    token_data = response.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    # Save both tokens (assuming your Credentials model has a field `token_type`)
    if access_token:
        Credentials.objects.create(
            client_id=client_id,
            client_secret=client_secret,
            token_type="access_token",
            token=access_token,
        )

    if refresh_token:
        Credentials.objects.create(
            client_id=client_id,
            client_secret=client_secret,
            token_type="refresh_token",
            token=refresh_token,
        )


def read_gmail(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages", headers=headers
    )
    return res.json()
