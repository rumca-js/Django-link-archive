from pathlib import Path
import logging
from datetime import timedelta

from django.views import generic
from django.urls import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.forms.models import model_to_dict
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    UserConfig,
    BackgroundJob,
    AppLogging,
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
    EntryDataBuilder,
    EntriesUpdater,
    BackgroundJobController,
)
from ..configuration import Configuration
from ..forms import (
    ConfigForm,
    UserConfigForm,
)
from ..views import ViewPage
from ..webtools import selenium_feataure_enabled
from ..dateutils import DateUtils


def index(request):
    p = ViewPage(request)
    p.set_title("Index")
    if p.is_user_allowed(ConfigurationEntry.ACCESS_TYPE_ALL):
        return redirect("{}:entries-omni-search-init".format(LinkDatabase.name))
    else:
        exports = DataExport.get_public_export_names()
        p.context["public_exports"] = exports

        # we forcefully display about page. Always. It is a feature.
        return p.render_implementation("about.html")


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

    configuration_entry = ConfigurationEntry.get()
    form = ConfigForm(instance=configuration_entry, request=request)

    form.method = "POST"
    form.action_url = reverse("{}:configuration-advanced".format(LinkDatabase.name))

    p.set_variable("config_form", form)

    errors = []

    if (configuration_entry.days_to_move_to_archive > 0 and
       configuration_entry.days_to_remove_links > 0 and
       configuration_entry.days_to_remove_links < configuration_entry.days_to_move_to_archive):
       errors.append("Links are removed before they can get to archive. Check your configuration")

    if (configuration_entry.whats_new_days > 0 and configuration_entry.days_to_remove_links > 0 and
       configuration_entry.whats_new_days > configuration_entry.days_to_remove_links):
       errors.append("Links are removed before limit of whats new filter")

    if configuration_entry.data_export_path != "" and not Path(configuration_entry.data_export_path).exists():
        errors.append(f"Data export directory does not exist:{configuration_entry.data_export_path}")

    if configuration_entry.data_import_path != "" and not Path(configuration_entry.data_import_path).exists():
        errors.append(f"Data import directory does not exist:{configuration_entry.data_import_path}")

    if configuration_entry.admin_user != "" and User.objects.filter(username = configuration_entry.admin_user).count() == 0:
        errors.append(f"Admin user does not exist:{configuration_entry.admin_user}")

    if len(errors) > 0:
        p.set_variable("form_errors", errors)

    return p.render("form_configuration.html")


def configuration_advanced_json(request):
    p = ViewPage(request)
    p.set_title("Configuration JSON")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    config = ConfigurationEntry.get()

    json_obj = model_to_dict(config)

    # JsonResponse
    return JsonResponse(json_obj)


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
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)

    # we forcefully display about page. Always. It is a feature.
    return p.render_implementation("about.html")


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
    p.context["selenium_feataure_enabled"] = selenium_feataure_enabled

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
    if entries:
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

    now = c.get_local_time(DateUtils.get_datetime_now_utc())
    p.context["DateTime_Current"] = now

    current_time = DateUtils.get_datetime_now_utc()

    conf = c.config_entry
    if conf.days_to_move_to_archive != 0:
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)
        p.context["days_to_move_to_archive"] = c.get_local_time(days_before)

    if conf.days_to_remove_links != 0:
        days_before = current_time - timedelta(days=conf.days_to_remove_links)
        p.context["days_to_remove_links"] = c.get_local_time(days_before)

    if conf.days_to_remove_stale_entries != 0:
        days_before = current_time - timedelta(days=conf.days_to_remove_stale_entries)
        p.context["days_to_remove_stale_entries"] = c.get_local_time(days_before)

    if conf.days_to_check_std_entries != 0:
        days_before = current_time - timedelta(days=conf.days_to_check_std_entries)
        p.context["days_to_check_std_entries"] = c.get_local_time(days_before)

    if conf.days_to_check_stale_entries != 0:
        days_before = current_time - timedelta(days=conf.days_to_check_stale_entries)
        p.context["days_to_check_stale_entries"] = c.get_local_time(days_before)

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
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(AppLoggingView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(AppLoggingView, self).get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)
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


def truncate_log_warnings(request):
    p = ViewPage(request)
    p.set_title("Clearing warnings logs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    AppLogging.objects.filter(level=logging.WARNING).delete()

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
Other
"""


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
    c.keep_domains = False
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
    c.keep_domains = False
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
    c.keep_domains = True
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


def setup_default_rules(request):
    p = ViewPage(request)
    p.set_title("Entry rule update")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    EntryRules.update_link_service_rule()
    EntryRules.update_webspam_rule()

    p.context["summary_text"] = "Updated rules"
    return p.render("summary_present.html")


def is_system_ok(request):
    """
    Some parts are configured by celery.
    Assumming tasks run faster than 1 hour.
    """
    p = ViewPage(request)
    p.set_title("Is systme OK")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    system_is_ok = SystemOperation.is_system_healthy()

    text = "YES" if system_is_ok else "NO"
    status_code = 200 if system_is_ok else 500

    return HttpResponse(text, status=status_code)
