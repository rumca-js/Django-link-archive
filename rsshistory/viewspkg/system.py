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

from webtools import selenium_feataure_enabled
from utils.dateutils import DateUtils

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
    UserCommentsController,
    EntryDataBuilder,
    EntriesUpdater,
    BackgroundJobController,
)
from ..configuration import Configuration
from ..serializers import JsonImporter
from ..forms import (
    ConfigForm,
    UserConfigForm,
)
from ..views import ViewPage


def index(request):
    p = ViewPage(request)
    p.set_title("Index")

    if p.is_user_allowed(ConfigurationEntry.ACCESS_TYPE_ALL):
        entry = ConfigurationEntry.get()
        if not entry.initialized:
            return redirect("{}:wizard".format(LinkDatabase.name))
        else:
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

    if (
        configuration_entry.days_to_move_to_archive > 0
        and configuration_entry.days_to_remove_links > 0
        and configuration_entry.days_to_remove_links
        < configuration_entry.days_to_move_to_archive
    ):
        errors.append(
            "Links are removed before they can get to archive. Check your configuration"
        )

    if (
        configuration_entry.whats_new_days > 0
        and configuration_entry.days_to_remove_links > 0
        and configuration_entry.whats_new_days
        > configuration_entry.days_to_remove_links
    ):
        errors.append("Links are removed before limit of whats new filter")

    if (
        configuration_entry.data_export_path != ""
        and not Path(configuration_entry.data_export_path).exists()
    ):
        errors.append(
            f"Data export directory does not exist:{configuration_entry.data_export_path}"
        )

    if (
        configuration_entry.data_import_path != ""
        and not Path(configuration_entry.data_import_path).exists()
    ):
        errors.append(
            f"Data import directory does not exist:{configuration_entry.data_import_path}"
        )

    if (
        configuration_entry.admin_user != ""
        and User.objects.filter(username=configuration_entry.admin_user).count() == 0
    ):
        errors.append(f"Admin user does not exist:{configuration_entry.admin_user}")

    if configuration_entry.instance_internet_location == "":
        errors.append(f"Instance Internet location was not configured properly")

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

    last_internet_check = c.get_local_time(SystemOperation.get_last_internet_check())
    p.context["last_internet_check"] = last_internet_check

    p.context["ConfigurationEntry"] = ConfigurationEntry.objects.count()
    p.context["UserConfig"] = UserConfig.objects.count()
    p.context["SystemOperation"] = SystemOperation.objects.count()

    p.context["SourceDataModel"] = SourceDataController.objects.count()
    p.context["LinkDataModel"] = LinkDataController.objects.count()
    p.context["ArchiveLinkDataModel"] = ArchiveLinkDataController.objects.count()
    p.context["KeyWords"] = KeyWords.objects.count()

    # u = EntriesUpdater()
    # entries = u.get_entries_to_update()
    # if entries:
    #    p.context["LinkDataModel_toupdate"] = entries.count()

    p.context["UserTags"] = UserTags.objects.count()
    p.context["UserVotes"] = UserVotes.objects.count()
    p.context["UserBookmarks"] = UserBookmarks.objects.count()
    p.context["UserCommentsController"] = UserCommentsController.objects.count()
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


def init_sources(request):
    if "noinitialize" not in request.GET:
        path = Path("init_sources.json")
        if path.exists():
            i = JsonImporter(path)
            i.import_all()


def init_selenium_driver(configuration_entry):
    p = Path("/usr/bin/chromedriver")
    if p.exists():
        configuration_entry.selenium_driver_path = str(p)


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

    c.initialized = True

    init_selenium_driver(c)
    c.save()

    init_sources(request)

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

    c.initialized = True

    init_selenium_driver(c)
    c.save()

    init_sources(request)

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

    c.initialized = True

    init_selenium_driver(c)
    c.save()

    init_sources(request)

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


def opensearchxml(request):
    """
    https://developer.mozilla.org/en-US/docs/Web/OpenSearch
    example: https://sjp.pwn.pl/opensearch.xml
    example: https://whoogle.io/opensearch.xml
    """

    p = ViewPage(request)
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    config = ConfigurationEntry.get()

    text = ""

    if config.instance_internet_location:
        text = """

      <OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/"
                             xmlns:moz="http://www.mozilla.org/2006/browser/search/">
        <ShortName>{config.instance_title}</ShortName>
        <Description>{config.instance_description}</Description>
        <InputEncoding>[UTF-8]</InputEncoding>

        <Image width="60" height="60" type="image/png"> data:image/png;base64,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o2z1LfT1DtJ3fSBR0oPAsyjVhIgpTc+uA6jR0VGx293AAVJYsJYMDMOgq+M6TqeD0vLimP7X6UqnpGwVLU0djAyPJUL6OCL/iUjoyM+fMwnX1FZTufsgiAwC9wN58b5yMyAihMM67W095OZlsap4ZUx3lpnlIic3m4b61nhr5QngWUyXRM35UzPz1bNzP2K19mMYOcB+lknKIkLAH6S9rZvi0pXkF8Qe+0L3CjIznTQ3thPwB+cj/Q4iP0YkMLUxPk24prYaz9a9AO2YSb1FW+xUkPZ6J+nrHaSsojimjxYRClfm09PdT1fH9ViEe4F/AS7Z3W7OnD4GzA40LBYwjJZI0dfgchEG0801N7bz5mvvMDgwPOd+wB+k+vdnqL/chMxVxhDwEpr2O0T4yY/+fobijU/V1Fbj2bkfoBkzCNnDMqk2mFIc6B/G651kw8YKbJF6EZ/Pz9u/fp/33q7G552MJd33gGdQajxuyUPN+VN4tu8zEKkHtmDmc5cVvT39WKwWVlcUMzo8zltv/o6PPqwhHIoZddUh8o+I1E8ZqgUJA1TuOgC6PoZILbAVKGMZoesG7S1d+LyTfHSyhnM1ddOVQ7PQBnxn5I03Tjq2bk28bAmm6z0A9gIvY27HLDvmIQowgMj3gZ+hlJqvon7e1dGRV58HTYOXn/s/RL6NWfS17JiHbDsi30fkF4iohY4PLBg319RW4+nSQal24DRmBe0altGQxUAd8B3gKEoZ8UqJ4y4Uamqrqdx1AKXrA6Jpp4EsTEO23EWmIcyw8Xtit1ejlEqkbjq5AnFzXrswkwX/DKSkCGMR6AVeAo4A/RCZggkgadW84azDDsw6zMf44uqnJ4D3gZfRtBMoFUr27MPiD3mYxwHsGMYdwCHgIGY4ejPm9xBQDfwSkeNK10cdbjc/+fF3k/7Q0o/xPP40mBtVm1Hqy5jnIHaw9NMtQaABOAH8FpFPEfFiGAmr700hPE185gCIG7OA5DbMQpm1mEnCDMyyCuusdnXMJLkPM5XaDnwGnEXkLCLti1Hdm044irwpdUEpJ5APFKNUKSK3RDbgZ47iwRjQjUgX0AFcR2QcMBI5tJEs/h/GMBxGKn9DKwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMC0wNC0xMlQyMDoyMDo0OSswMDowME0is3UAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjAtMDQtMTJUMjA6MjA6NDkrMDA6MDA8fwvJAAAARnRFWHRzb2Z0d2FyZQBJbWFnZU1hZ2ljayA2LjcuOC05IDIwMTQtMDUtMTIgUTE2IGh0dHA6Ly93d3cuaW1hZ2VtYWdpY2sub3Jn3IbtAAAAABh0RVh0VGh1bWI6OkRvY3VtZW50OjpQYWdlcwAxp/+7LwAAABh0RVh0VGh1bWI6OkltYWdlOjpoZWlnaHQAMTkyDwByhQAAABd0RVh0VGh1bWI6OkltYWdlOjpXaWR0aAAxOTLTrCEIAAAAGXRFWHRUaHVtYjo6TWltZXR5cGUAaW1hZ2UvcG5nP7JWTgAAABd0RVh0VGh1bWI6Ok1UaW1lADE1ODY3MjI4NDlV2OpiAAAAD3RFWHRUaHVtYjo6U2l6ZQAwQkKUoj7sAAAAVnRFWHRUaHVtYjo6VVJJAGZpbGU6Ly8vbW50bG9nL2Zhdmljb25zLzIwMjAtMDQtMTIvNTdhMDYyNGFhNzAyYzk3ZWU1YTE5MjgwYWEwNTkwZDMuaWNvLnBuZ1EXWHMAAAAASUVORK5CYII=</Image>

        <Url type="text/html" template="{config.instance_internet_location}/entries-omni-search?search={searchTerms}"/>
        <Url type="application/x-suggestions+json" template="{config.instance_internet_location}/search-suggestions">
            <Param name="search" value="{searchTerms}"/>
        </Url>

      </OpenSearchDescription>
        """
        text = text.replace("{config.instance_title}", config.instance_title)
        text = text.replace(
            "{config.instance_description}", config.instance_description
        )
        text = text.replace(
            "{config.instance_internet_location}", config.instance_internet_location
        )

    status_code = 200
    content_type = "application/opensearchdescription+xml"

    return HttpResponse(text, status=status_code, content_type=content_type)


def search_suggestions(request):
    """
    We could implement search suggestions based on history.
    Wouldn't it be too performance taxing?
    """

    status_code = 200
    content_type = "text/html"
    text = "[]"

    return HttpResponse(text, status=status_code, content_type=content_type)
