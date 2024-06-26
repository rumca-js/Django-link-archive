from pathlib import Path
import logging

from django.views import generic
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    UserConfig,
    BackgroundJob,
    AppLogging,
    SourceExportHistory,
    Domains,
    UserTags,
    UserVotes,
    UserBookmarks,
    UserSearchHistory,
    UserEntryVisitHistory,
    UserEntryTransitionHistory,
    KeyWords,
    SystemOperation,
    DataExport,
    SourceExportHistory,
    ModelFiles,
)
from ..controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    LinkCommentDataController,
    BackgroundJobController,
    EntryDataBuilder,
    EntriesUpdater,
    BackgroundJobController,
)
from ..configuration import Configuration
from ..forms import (
    ConfigForm,
    UserConfigForm,
    BackgroundJobForm,
    LinkInputForm,
    ScannerForm,
    UrlContentsForm,
)
from ..views import ViewPage
from ..pluginurl.urlhandler import UrlHandler
from ..webtools import ContentLinkParser, RssPage


def index(request):
    p = ViewPage(request)
    p.set_title("Index")
    return p.render("index.html")


"""
Configuration views
"""


def admin_page(request):
    p = ViewPage(request)
    p.set_title("Admin")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data
    return p.render("admin_page.html")


def configuration_advanced_page(request):
    p = ViewPage(request)
    p.set_title("Configuration")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ob = ConfigurationEntry.get()

    if request.method == "POST":
        form = ConfigForm(request.POST, instance=ob, request=request)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                reverse("{}:admin-page".format(LinkDatabase.name))
            )
        else:
            p.set_variable("summary_text", "Form is invalid")
            return p.render("summary_present.html")

    ob = ConfigurationEntry.get()
    form = ConfigForm(instance=ob, request=request)

    form.method = "POST"
    form.action_url = reverse("{}:configuration-advanced".format(LinkDatabase.name))

    p.set_variable("config_form", form)

    return p.render("configuration.html")


def user_config(request):
    p = ViewPage(request)
    p.set_title("User configuration")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    user_obj = UserConfig.get_or_create(request.user)

    if request.method == "POST":
        form = UserConfigForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
        else:
            p.context["summary_text"] = "user information is not valid, cannot save"
            return p.render("summary_present.html")
    else:
        form = UserConfigForm(instance=user_obj)

    form.method = "POST"
    form.action_url = reverse("{}:user-config".format(LinkDatabase.name))

    p.context["config_form"] = form
    p.context["user_object"] = user_obj

    return p.render("user_configuration.html")


"""
Status views
"""


def about(request):
    p = ViewPage(request)
    p.set_title("About")
    return p.render("about.html")


def missing_rights(request):
    p = ViewPage(request)
    p.set_title("Missing rights")
    p.context["summary_text"] = "user information is not valid, cannot save"
    return p.render("summary_present.html")


def system_status(request):
    p = ViewPage(request)
    p.set_title("Status")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    c = Configuration.get_object()
    p.context["directory"] = c.directory

    p.context["last_internet_status"] = SystemOperation.get_last_internet_status()

    last_internet_check = c.get_local_time(SystemOperation.get_last_internet_check())
    p.context["last_internet_check"] = last_internet_check

    p.context["ConfigurationEntry"] = ConfigurationEntry.objects.count()
    p.context["UserConfig"] = UserConfig.objects.count()
    p.context["SystemOperation"] = SystemOperation.objects.count()

    p.context["SourceDataModel"] = SourceDataController.objects.count()
    p.context["LinkDataModel"] = LinkDataController.objects.count()
    p.context["ArchiveLinkDataModel"] = ArchiveLinkDataController.objects.count()
    p.context["KeyWords"] = KeyWords.objects.count()

    u = EntriesUpdater()
    entries = u.get_entries_to_update()
    p.context["LinkDataModel_toupdate"] = entries.count()

    p.context["UserTags"] = UserTags.objects.count()
    p.context["UserVotes"] = UserVotes.objects.count()
    p.context["UserBookmarks"] = UserBookmarks.objects.count()
    p.context["LinkCommentDataController"] = LinkCommentDataController.objects.count()
    p.context["UserSearchHistory"] = UserSearchHistory.objects.count()
    p.context["UserEntryVisitHistory"] = UserEntryVisitHistory.objects.count()
    p.context["UserEntryTransitionHistory"] = UserEntryTransitionHistory.objects.count()

    p.context["BackgroundJob"] = BackgroundJob.objects.count()
    p.context["DataExport"] = DataExport.objects.count()
    p.context["SourceExportHistory"] = SourceExportHistory.objects.count()
    p.context["ModelFiles"] = ModelFiles.objects.count()

    from ..dateutils import DateUtils
    from datetime import timedelta

    now = c.get_local_time(DateUtils.get_datetime_now_utc())
    p.context["DateTime_Current"] = now

    conf = c.config_entry
    if conf.days_to_move_to_archive != 0:
        current_time = DateUtils.get_datetime_now_utc()
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)
        p.context["DateTime_MoveToArchive"] = c.get_local_time(days_before)

    p.context["AppLogging"] = AppLogging.objects.count()
    p.context["Domains"] = Domains.objects.count()

    p.context["server_path"] = Path(".").resolve()
    p.context["directory"] = Path(".").resolve()

    history = SourceExportHistory.get_safe()
    p.context["export_history_list"] = history

    return p.render("system_status.html")


class AppLoggingView(generic.ListView):
    model = AppLogging
    context_object_name = "content_list"

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(AppLoggingView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(AppLoggingView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)
        context["page_title"] += " Logs"

        return context


def truncate_log_all(request):
    p = ViewPage(request)
    p.set_title("Clearing all logs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    AppLogging.truncate()

    return HttpResponseRedirect(reverse("{}:logs".format(LinkDatabase.name)))


def truncate_log(request):
    p = ViewPage(request)
    p.set_title("Clearing info logs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    AppLogging.objects.filter(level__lt=40).delete()

    return HttpResponseRedirect(reverse("{}:logs".format(LinkDatabase.name)))


def truncate_log_errors(request):
    p = ViewPage(request)
    p.set_title("Clearing error logs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    AppLogging.objects.filter(level=logging.ERROR).delete()

    return HttpResponseRedirect(reverse("{}:logs".format(LinkDatabase.name)))


def reset_config(request):
    p = ViewPage(request)
    p.set_title("Reset configuration")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    Configuration.get_object().config_entry = ConfigurationEntry.get()

    p.context["summary_text"] = "Configuration is reset"
    return p.render("summary_present.html")


"""
Background jobs
"""


class BackgroundJobsView(generic.ListView):
    model = BackgroundJobController
    context_object_name = "content_list"
    paginate_by = 500
    template_name = str(ViewPage.get_full_template("backgroundjob_list.html"))

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(BackgroundJobsView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BackgroundJobsView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        context["BackgroundJob"] = BackgroundJob.objects.count()
        context["page_title"] += " Jobs"

        return context


def backgroundjob_add(request):
    p = ViewPage(request)
    p.set_title("Add a new background job")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = BackgroundJobForm(request.POST)
        if form.is_valid():
            BackgroundJobController.objects.create(**form.cleaned_data)

            return HttpResponseRedirect(
                reverse("{}:backgroundjobs".format(LinkDatabase.name))
            )
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    form = BackgroundJobForm()
    form.method = "POST"
    form.action_url = reverse("{}:backgroundjob-add".format(LinkDatabase.name))

    p.context["form"] = form

    return p.render("form_basic.html")


def backgroundjob_prio_up(request, pk):
    p = ViewPage(request)
    p.set_title("Increment job priority")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.filter(id=pk)
    if jobs.count() > 0:
        job = jobs[0]
        job.priority -= 1
        job.save()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjob_prio_down(request, pk):
    p = ViewPage(request)
    p.set_title("Decrement job priority")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.filter(id=pk)
    if jobs.count() > 0:
        job = jobs[0]
        job.priority += 1
        job.save()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjob_enable(request, pk):
    p = ViewPage(request)
    p.set_title("Enable job")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.filter(id=pk)
    if jobs.count() > 0:
        jobs[0].enable()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjob_disable(request, pk):
    p = ViewPage(request)
    p.set_title("Disable job")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.filter(id=pk)
    if jobs.count() > 0:
        jobs[0].disable()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjob_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove a new background job")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.filter(id=pk)
    if jobs.count() > 0:
        jobs.delete()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_remove_all(request):
    p = ViewPage(request)
    p.set_title("Remove all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    bg = BackgroundJobController.objects.all()
    bg.delete()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_check_new(request):
    p = ViewPage(request)
    p.set_title("Check for new background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..threadhandlers import RefreshThreadHandler

    refresh_handler = RefreshThreadHandler()
    refresh_handler.refresh()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_perform_all(request):
    p = ViewPage(request)
    p.set_title("Process all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..threadhandlers import HandlerManager, RefreshThreadHandler

    mgr = HandlerManager()
    mgr.process_all()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_enable_all(request):
    p = ViewPage(request)
    p.set_title("Enables all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.all()
    for job in jobs:
        job.enabled = True
        job.save()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_disable_all(request):
    p = ViewPage(request)
    p.set_title("Disables all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.all()
    for job in jobs:
        job.enabled = False
        job.save()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_remove(request, job_type):
    p = ViewPage(request)
    p.set_title("Remove background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.filter(job=job_type)
    jobs.delete()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


"""
Keywords
"""


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


"""
Other
"""


def reset_cache(request):
    p = ViewPage(request)
    p.set_title("Reset cache")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from django.core.cache import cache
    cache.clear()

    return HttpResponseRedirect(reverse("{}:admin-page".format(LinkDatabase.name)))


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
                    summary += "<a href='{}'>{}:{}</a>,".format(
                        entry.get_absolute_url(), prop["link"], prop["title"]
                    )

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


def wizard_setup(request):
    p = ViewPage(request)
    p.set_title("Select setup")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    return p.render("wizard_setup.html")


def wizard_setup_news(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    p = ViewPage(request)
    p.set_title("Sets configuration for news")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    c = ConfigurationEntry.get()
    c.link_save = True
    c.source_save = False
    c.accept_dead = False
    c.accpte_ip_addresses = False
    c.auto_scan_entries = False
    c.accept_not_domain_entries = True
    c.auto_store_sources = False
    c.accept_domains = False
    c.enable_keyword_support = True
    c.track_user_actions = True
    c.track_user_searches = True
    c.track_user_navigation = False
    c.days_to_move_to_archive = 100
    c.days_to_check_stale_entries = 10
    c.days_to_remove_links = 20
    c.days_to_remove_stale_entries = 0  # do not remove bookmarks?
    c.whats_new_days = 7
    c.prefer_https = False
    c.entries_order_by = "-date_published, link"
    c.display_type = ConfigurationEntry.DISPLAY_TYPE_STANDARD

    c.save()

    p.context["summary_text"] = "Set configuration for news"

    return p.render("summary_present.html")


def wizard_setup_gallery(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    p = ViewPage(request)
    p.set_title("Sets configuration for news")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    c = ConfigurationEntry.get()
    c.link_save = False
    c.source_save = False
    c.accept_dead = False
    c.accpte_ip_addresses = False
    c.auto_scan_entries = False
    c.accept_not_domain_entries = True
    c.auto_store_sources = False
    c.accept_domains = False
    c.enable_keyword_support = False
    c.track_user_actions = True
    c.track_user_searches = True
    c.track_user_navigation = True
    c.days_to_move_to_archive = 0
    c.days_to_check_stale_entries = 10
    c.days_to_remove_links = 30
    c.days_to_remove_stale_entries = 0  # do not remove bookmarks?
    c.whats_new_days = 7
    c.prefer_https = False
    c.entries_order_by = "-date_published, link"
    c.display_type = ConfigurationEntry.DISPLAY_TYPE_GALLERY

    c.save()

    p.context["summary_text"] = "Set configuration for gallery"

    return p.render("summary_present.html")


def wizard_setup_search_engine(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    p = ViewPage(request)
    p.set_title("Sets configuration for news")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    c = ConfigurationEntry.get()
    c.link_save = False
    c.source_save = False
    c.accept_dead = False
    c.accpte_ip_addresses = False
    c.auto_scan_entries = True
    c.accept_not_domain_entries = True
    c.auto_store_sources = True
    c.accept_domains = True
    c.enable_keyword_support = False
    c.track_user_actions = True
    c.track_user_searches = True
    c.track_user_navigation = (
        False  # it would be interesting for the search engine though
    )
    c.days_to_move_to_archive = 0
    c.days_to_check_stale_entries = 10
    c.days_to_remove_links = 30
    c.days_to_remove_stale_entries = 30
    c.whats_new_days = 7
    c.prefer_https = True
    c.entries_order_by = "-page_rating, link"
    c.display_type = ConfigurationEntry.DISPLAY_TYPE_SEARCH_ENGINE

    c.save()

    p.context["summary_text"] = "Set configuration for search engine"

    return p.render("summary_present.html")
