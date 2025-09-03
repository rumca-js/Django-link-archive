from pathlib import Path
import time
import logging
from datetime import timedelta
import os

from django.templatetags.static import static
from django.views import generic
from django.urls import reverse
from django.utils.html import escape
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Q


from utils.dateutils import DateUtils
from utils.systemmonitoring import get_hardware_info

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    UserConfig,
    BackgroundJob,
    BackgroundJobHistory,
    AppLogging,
    ApiKeys,
    Domains,
    UserTags,
    UserCompactedTags,
    CompactedTags,
    EntryCompactedTags,
    UserVotes,
    UserBookmarks,
    UserSearchHistory,
    UserEntryVisitHistory,
    UserEntryTransitionHistory,
    KeyWords,
    BlockEntry,
    BlockEntryList,
    SocialData,
    SystemOperation,
    DataExport,
    SourceExportHistory,
    SourceOperationalData,
    ModelFiles,
    ReadLater,
    EntryRules,
    SearchView,
)
from ..controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    UserCommentsController,
    EntryDataBuilder,
    EntriesUpdater,
    BackgroundJobController,
    SystemOperationController,
    system_setup_for_news,
    system_setup_for_gallery,
    system_setup_for_search_engine,
)
from ..configuration import Configuration
from ..serializers import JsonImporter
from ..forms import (
    ConfigForm,
    UserConfigForm,
)
from ..views import ViewPage, SimpleViewPage, get_search_view


def index(request):
    p = ViewPage(request, ConfigurationEntry.ACCESS_TYPE_ALL)
    p.set_title("Index")

    if p.is_allowed():
        config = Configuration.get_object().config_entry
        if not config.initialized:
            return redirect("{}:wizard-init".format(LinkDatabase.name))
        else:
            search_view = get_search_view(request)
            if search_view.auto_fetch:
                url = reverse(f"{LinkDatabase.name}:entries")
            else:
                url = reverse(f"{LinkDatabase.name}:entries")
            return HttpResponseRedirect(url)
    else:
        exports = DataExport.get_public_export_names()
        p.context["public_exports"] = exports

        # we forcefully display about page. Always. It is a feature.
        return p.render_implementation("about.html")


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
            error_message = "\n".join(
                [
                    "{}: {}".format(field, ", ".join(errors))
                    for field, errors in form.errors.items()
                ]
            )

            p.context["summary_text"] = "Form is invalid: {}".format(error_message)
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
        configuration_entry.data_export_path != ""
        and not Path(configuration_entry.get_export_path_abs()).exists()
    ):
        errors.append(
            f"Data export directory does not exist:{configuration_entry.data_export_path}"
        )

    if (
        configuration_entry.data_import_path != ""
        and not Path(configuration_entry.get_import_path_abs()).exists()
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
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    config = ConfigurationEntry.get()

    json_obj = model_to_dict(config)

    return JsonResponse(json_obj, json_dumps_params={"indent": 4})


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

    return p.render("user_config.html")


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

    return p.render("system_status.html")


def json_table_status(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    table = []

    table.append({"name": "LinkDataModel", "count": LinkDataController.objects.count()})
    table.append(
        {
            "name": "ArchiveLinkDataModel",
            "count": ArchiveLinkDataController.objects.count(),
        }
    )

    table.append(
        {"name": "SourceDataModel", "count": SourceDataController.objects.count()}
    )
    table.append(
        {
            "name": "SourceOperationalData",
            "count": SourceOperationalData.objects.count(),
        }
    )

    table.append(
        {"name": "ConfigurationEntry", "count": ConfigurationEntry.objects.count()}
    )

    table.append({"name": "BackgroundJob", "count": BackgroundJob.objects.count()})
    table.append(
        {"name": "BackgroundJobHistory", "count": BackgroundJobHistory.objects.count()}
    )
    table.append({"name": "AppLogging", "count": AppLogging.objects.count()})

    table.append({"name": "UserConfig", "count": UserConfig.objects.count()})
    table.append({"name": "SystemOperation", "count": SystemOperation.objects.count()})

    table.append({"name": "KeyWords", "count": KeyWords.objects.count()})
    table.append({"name": "BlockEntry", "count": BlockEntry.objects.count()})
    table.append({"name": "BlockEntryList", "count": BlockEntryList.objects.count()})

    table.append({"name": "SocialData", "count": SocialData.objects.count()})
    table.append({"name": "UserTags", "count": UserTags.objects.count()})
    table.append(
        {"name": "UserCompactedTags", "count": UserCompactedTags.objects.count()}
    )
    table.append({"name": "CompactedTags", "count": CompactedTags.objects.count()})
    table.append(
        {"name": "EntryCompactedTags", "count": EntryCompactedTags.objects.count()}
    )
    table.append({"name": "UserVotes", "count": UserVotes.objects.count()})
    table.append({"name": "UserBookmarks", "count": UserBookmarks.objects.count()})
    table.append(
        {"name": "UserComments", "count": UserCommentsController.objects.count()}
    )
    table.append(
        {"name": "UserSearchHistory", "count": UserSearchHistory.objects.count()}
    )
    table.append(
        {
            "name": "UserEntryVisitHistory",
            "count": UserEntryVisitHistory.objects.count(),
        }
    )
    table.append(
        {
            "name": "UserEntryTransitionHistory",
            "count": UserEntryTransitionHistory.objects.count(),
        }
    )

    table.append({"name": "DataExport", "count": DataExport.objects.count()})
    table.append(
        {"name": "SourceExportHistory", "count": SourceExportHistory.objects.count()}
    )
    table.append({"name": "ModelFiles", "count": ModelFiles.objects.count()})
    table.append({"name": "Domains", "count": Domains.objects.count()})

    # u = EntriesUpdater()
    # entries = u.get_entries_to_update()
    # if entries:
    #    p.context["LinkDataModel_toupdate"] = entries.count()

    data = {}
    data["tables"] = table

    return JsonResponse(data, json_dumps_params={"indent": 4})


def json_system_status(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    data = {}

    c = Configuration().get_object()

    system_controller = SystemOperationController()

    last_internet_check = c.get_local_time(
        system_controller.last_operation_status_date()
    )
    data["last_internet_check"] = last_internet_check

    last_internet_status = system_controller.last_operation_status()
    data["last_internet_status"] = last_internet_status

    last_crawling_server_check = c.get_local_time(
        system_controller.last_operation_status_date(
            SystemOperation.CHECK_TYPE_CRAWLING_SERVER
        )
    )

    data["last_crawling_server_check"] = last_crawling_server_check

    last_crawling_server_status = system_controller.last_operation_status(
        SystemOperation.CHECK_TYPE_CRAWLING_SERVER
    )
    data["last_crawling_server_status"] = last_crawling_server_status

    now = c.get_local_time(DateUtils.get_datetime_now_utc())
    data["current_time"] = now

    current_time = DateUtils.get_datetime_now_utc()

    conf = c.config_entry
    if conf.days_to_move_to_archive != 0:
        days_before = current_time - timedelta(days=conf.days_to_move_to_archive)
        data["days_to_move_to_archive"] = days_before
    else:
        data["days_to_move_to_archive"] = 0

    if conf.days_to_remove_links != 0:
        days_before = current_time - timedelta(days=conf.days_to_remove_links)
        data["days_to_remove_links"] = days_before
    else:
        data["days_to_remove_links"] = 0

    if conf.days_to_remove_stale_entries != 0:
        days_before = current_time - timedelta(days=conf.days_to_remove_stale_entries)
        data["days_to_remove_stale_entries"] = days_before
    else:
        data["days_to_remove_stale_entries"] = 0

    if conf.days_to_check_std_entries != 0:
        days_before = current_time - timedelta(days=conf.days_to_check_std_entries)
        data["days_to_check_std_entries"] = days_before
    else:
        data["days_to_check_std_entries"] = 0

    if conf.days_to_check_stale_entries != 0:
        days_before = current_time - timedelta(days=conf.days_to_check_stale_entries)
        data["days_to_check_stale_entries"] = days_before
    else:
        data["days_to_check_stale_entries"] = 0

    data["current_time"] = current_time

    # is_remote_server_down = system_controller.is_remote_server_down()
    # data["remote_server_status"] = is_remote_server_down

    data["directory"] = c.directory

    data["threads"] = []

    threads = SystemOperationController.get_threads()
    for thread_id in threads:
        thread_info = system_controller.get_thread_info(thread_id)
        data["threads"].append(
            {"name": thread_id, "date": thread_info[1], "status": thread_info[2]}
        )

    return JsonResponse(data, json_dumps_params={"indent": 4})


def json_system_monitoring(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    data = get_hardware_info()

    return JsonResponse(data, json_dumps_params={"indent": 4})


def history_to_json(history):
    json = {}
    json["date"] = history.date
    json["export_type"] = history.export.export_type
    json["export_data"] = history.export.export_data
    json["remote_path"] = history.export.remote_path
    json["local_path"] = history.export.local_path
    return json


def json_settings(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    configuration = Configuration.get_object()
    data = configuration.get_settings()

    return JsonResponse(data, json_dumps_params={"indent": 4})


def json_export_status(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    data = {}
    data["exports"] = []

    histories = SourceExportHistory.get_safe()
    for history in histories:
        data["exports"].append(history_to_json(history))

    return JsonResponse(data, json_dumps_params={"indent": 4})


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


def log_to_json(applogging_entry):
    json = {}

    json["id"] = applogging_entry.id
    json["is_info"] = applogging_entry.is_info()
    json["is_notification"] = applogging_entry.is_notification()
    json["is_warning"] = applogging_entry.is_warning()
    json["is_error"] = applogging_entry.is_error()
    json["date"] = applogging_entry.date
    json["level"] = applogging_entry.level
    json["id"] = applogging_entry.id

    json["info_text"] = escape(applogging_entry.info_text)
    json["detail_text"] = escape(applogging_entry.detail_text)

    return json


def json_logs(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_STAFF)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    data = {}
    data["logs"] = []
    data["count"] = 0
    data["num_pages"] = 0

    start_time = time.time()

    page_num = p.get_page_num()
    if page_num:
        conditions = Q()

        if "errors" in request.GET:
            conditions &= Q(level=AppLogging.ERROR)
        if "warnings" in request.GET:
            conditions &= Q(level=AppLogging.WARNING)
        if "infos" in request.GET:
            conditions &= Q(level=AppLogging.INFO)
        if "debugs" in request.GET:
            conditions &= Q(level=AppLogging.DEBUG)
        if "notification" in request.GET:
            conditions &= Q(level=AppLogging.NOTIFICATION)
        if "info_text" in request.GET:
            value = request.GET["info_text"]
            conditions &= Q(info_text__icontains=value)
        if "detail_text" in request.GET:
            value = request.GET["detail_text"]
            conditions &= Q(detail_text__icontains=value)

        objects = AppLogging.objects.filter(conditions)

        items_per_page = 500
        p = Paginator(objects, items_per_page)
        page_object = p.page(page_num)

        data["count"] = p.count
        data["num_pages"] = p.num_pages

        if page_num <= p.num_pages:
            for app_logging_entry in page_object:
                json_data = log_to_json(app_logging_entry)
                data["logs"].append(json_data)

        data["timestamp_s"] = time.time() - start_time

        return JsonResponse(data, json_dumps_params={"indent": 4})


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


def init_sources(request):
    if "noinitialize" not in request.GET:
        path = Path("init_sources.json")
        if path.exists():
            i = JsonImporter(path)
            i.import_all()


def get_sources_text():
    sources_link = reverse("{}:sources".format(LinkDatabase.name))
    link_string = (
        """<a href="{}?show=1" class="btn btn-secondary">Sources</a>""".format(
            sources_link
        )
    )
    return "You can navigate to sources to enable some of them: {}".format(link_string)


def wizard_setup(request):
    p = ViewPage(request)
    p.set_title("Select setup")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    UserConfig.get_or_create(request.user)

    return p.render("wizard_setup.html")


def wizard_setup_init(request):
    p = ViewPage(request)
    p.set_title("Select setup")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    UserConfig.get_or_create(request.user)

    return p.render("wizard_setup_init.html")


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

    system_setup_for_news(request)

    p.context["summary_text"] = "Set configuration for news."
    p.context["summary_text"] += get_sources_text()

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

    system_setup_for_gallery(request)

    p.context["summary_text"] = "Set configuration for gallery"
    p.context["summary_text"] += get_sources_text()

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

    system_setup_for_search_engine(request)

    p.context["summary_text"] = "Set configuration for search engine"
    p.context["summary_text"] += get_sources_text()

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
    p.set_title("Is system OK")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    system_controller = SystemOperationController()
    system_is_ok = system_controller.is_system_healthy()

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

        <Image width="60" height="60" type="image/png"> data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAYAAAA6/NlyAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAAASAAAAEgARslrPgAADS9JREFUaN7Nm2lsXNd1x3/nzQxnOMNdJEeUuYjUZu2Lh7IrWZZsy46btN7ioEgRSHZapEybLgHStPDSAqntNg7yIahdyAjgJg4aB66tJDBsy4ocW5QrWzYtUQslUdx3cV9nONt7tx/ekNSQQ84MOTLzB0hg3nbv/55zzzn33HOFm4Sqx58GEcEwHIALpXIQcaNUFmCJPKYQ8aJULyJDgBcRH4ZhHHn1+ZvSL0kZwX/9KTQ3g6bZgFKU2ghsBnYDxUAOkAnYAW2aMAQBLzAK9ALngLPANUQa8Psncbk48soP/jAIV33rBzA8DE5nHkp9CXggQnI14FjkZ8NAT4T4B8BvsNnaMQx15L//bXkIVz3+NFgsQihUDDwEPALcDriWOoizEAIuAb9B5KiIXFFK6Ud+/twXR7jq0JMAuRGSfwXsBGwpJjobBtACvAr8Ap+vhcxMkpV4UoSrDj8FIhpK7UKpfwK+DDhvMtHZ0IEziPwQOAYEk5F2QoSr/u4FGBkBkUyUOgz8A7DmCyY6G4PATxF5EcPowmLhyM+ejfuSJf53wbOhEqAA+Hfge0DhMpMFU7P2AFsQqUWpPs/2fdScP7U0wlWHngSRMuA54DCmW/lDgQBrgW3ANUpLOzwVO6iprV7whfhklXoR+Eq856eglPlPoeZvWASRlIUBAHWIfBvDOLWQes/bYsQSFwAvYEo2bu+UoUAg3elgRX4uK1cVkJuXjcNhR0QIhcJMjHvp7emn9/ogE+NewuEwmqbF+3Si+Bj4C5S6Mh/pmCSqDj8FkIlSLwB/CVgXJKoUIsLKogI2bV3Htp0bcRflk5HhxGqLftUwDPyTAUaGx7h2tYXaz+toberE7w+kSuLHEPlrTBfGbAs+p4Wqw0+B1SqEQn+DKd30eGRdGU7uPOBh710eCtwrkuq4zzvJlUuNHH+nmraWrlSRfgX4W8A3OyafY7Q82/eBUh7gR4A7Htni0iK+9udf4c4DlWRlZyTdYVuajVXFbtbdWk4oFKanqw9dN5ZKfC3Qgq5f8Ow6EGW5owjfEEH9B7BvoS8ahqJibQnf+ObDbNi0Bosl9jwMh3UCgSChYAgFaJoWk0xGposNGyswDIPWli4MXbEEznZgPZr2MXD9RsLTn6x64hkIBsFi+SbwIguoslKK4pIivn74QdasL5tzPxAI0t7aRXNDO91dfYyOjKHrBi5XOgWFeZRVFLN2XRnZuVlzyPt8kxz91TE+PvU5hjG/lU8Q/4WmfRcIThmwGYui62CxlADfikc2MyuDh752/xyyhmHQ0tjB74+fpv5KMxPjXpSa22m7PQ13UQF793vYvWc7TudMc05nOg9+9T7Gx7ycP3t5qar9VQzjdeBk1aEnOfLq86ZKVz3+NBgGiBwCnmBmvRoTB+69nbvu3o1oM53RdZ1TH3zG//7P2zQ1tBEKhqZ97ew/wzAYGR6n/koTA33DlK5ehdM1Q9ruSCNvRTaXLzbgn1yS9c4ADDTtXcCoOX8qQkwp0LQ8zNXPvC5IKcXKogLuuHMX2g1zVinFJx+d462jJxgaHJ13nt4ITRP0sM5nn5zn6K+OMToyHnV/dUUxO27btBTpTuEgSm2e+mGpeuIZU53hYaAKSJvvTRHhnvv3sLNycxShK5caefO1dxkbGUfTkpOGiHC9ux/RhPW3lk8HIZqmkZ7uSIWUs4FOLSPj1G2b7kDDMKbSMg9gqkBMKKVwudJZv7E8qvHJST8fnviYwYHhKBVPBqaGnOXa1Zao6yWrV7FmfVlMO5Ak/tjweotgZq6WApXxOlVYVMDKouiFUktjBw31rYgsPjwUEUZHxqk5cwE9rE9fT0uzUV5RkorQcwewA6XQUIpIwq083lv5Bbk4XdFpqsZrbUz6/EvxmdOkG6+1MTIyFnXdXVSA3Z4GSxOyC6V2EQ6jqXAYzOziggk3ESErOyNqtM3IqDcVKgfA+NgEY6MTUddy87KwO+wLrrwSxG5sNpcmNls6ZpYxLtLTo8dED+tzOrhYiJhWO+APRLfpdGCzJZSniIe1QL6GmWUsTuSNOZIUUr2mZfbcUIYiRQqUCxRrKJUb+RGHLUz6/FGXrFYruXlZKemNUgpbmhWnM1qLvN5JQqFwKprIQKlSDZFCFnBHM3wVw0Oj6PqMFbVaLZSUrUqJlJWCvBU5ZOdED+DgwDD+SX8q2nAgcosW2etJKE812D/MxLgv6tqadWVkZrlSYLgU6zaUk5UVPfa9PQMEg6ElDyhgQ6lcDXOJGNfRaaLR1ztId2dv1PXS1avYvG39ktyGUopCdz6Vf7QtKniZ9PlpbmhLmRcALIl7dDGjqrqL19B1Y2bY0mzcfd8eVpW4MQwj4c/dSNZms7L/3tspK4+2nU2N7TQ3daTUMGqYskl4CGs+uUhrc0fUtbLyW3j0zx6gwL0iKdJKKaxWC/vu3s3eA54oYsFAiE9P1zIx7kslYaUhMoG5ZRkXIsLw0CgnT3xCIBD9yuZt6/nGE4+wZp0Z+6oFFu9KKQzDICPTyZ88cpA/ffTgHB9/6UI9F89dTSVZHRizolQ/5v5sQhCBC+eusvHTi9xx523TblNEuHXzGvLyc/jow884//llhoZGCU4NjALEXAVlZWVQVlHMXffsZuOWtVitc1ek3Z29kUxmqvjiB7qtiAyi1GjihAW/P8BbR9/H7rCzq3JL1P1C9woefux+9t29m7bmTrq7+vBO+DAMA4fDTl5+Dqsriim6pRCHY37nsHe/h9bmTi7W1ie95JwHPkS6rJjS7U3mTRFhcGCEX7/+HjablS3bN0SpnmbRKCjMo6Awb/qaUiQlrdy8bB567D4mxr20NnUueul5A0aADkvl7oMhdH0TcbKUsUh7J3w01reaBN0rSEuzLfB88j3MzslkZVEBTQ1tTEws2XjVIvKKxbNlD5ih5aMk4I9nk56c9FN/uZn21i5cGU5y8rKxWBIL9pVS9PYMMDoyTlZ27GAvLz+HrOwM6i83E4zkyRaJ13E43rF4tu8DM4/1IGY6JCmICEop+q4PcrWukbbmTgKBoLmMFDN3NZXj0nWdgD/IyPAYrc0dnHz/DO/+9gPqLjRQvqaYrOzMmG0UuvPRRGht6iQcDi+GdBB4iXC4zhrRtQaU+hwoWezwaZowPublXE0dF8/Xk+Eypb0iPwdXhhNN0wj4zT2lwYFhxsa85lIwYr3feO1dvn7oQdxF+XO+bbVauOdLe/H7Axx/+9RiApxriJwFsHh27gfDCCNSBNxLgpvk80l7SuL+CLmerl7amrtoae6ks6OHgf4hfD4/RmQ7ZepvoG8I74SX9RsrYtoCi0WjuGQlA31DdHf1JivlX6JpbwCGpaa2Gs+Ou8AsE7oHKFos4VjkRQTRBE2Lzk3Hev56zwCGbrB2/Wos1rnjnmZPo2z1LfT1DtJ3fSBR0oPAsyjVhIgpTc+uA6jR0VGx293AAVJYsJYMDMOgq+M6TqeD0vLimP7X6UqnpGwVLU0djAyPJUL6OCL/iUjoyM+fMwnX1FZTufsgiAwC9wN58b5yMyAihMM67W095OZlsap4ZUx3lpnlIic3m4b61nhr5QngWUyXRM35UzPz1bNzP2K19mMYOcB+lknKIkLAH6S9rZvi0pXkF8Qe+0L3CjIznTQ3thPwB+cj/Q4iP0YkMLUxPk24prYaz9a9AO2YSb1FW+xUkPZ6J+nrHaSsojimjxYRClfm09PdT1fH9ViEe4F/AS7Z3W7OnD4GzA40LBYwjJZI0dfgchEG0801N7bz5mvvMDgwPOd+wB+k+vdnqL/chMxVxhDwEpr2O0T4yY/+fobijU/V1Fbj2bkfoBkzCNnDMqk2mFIc6B/G651kw8YKbJF6EZ/Pz9u/fp/33q7G552MJd33gGdQajxuyUPN+VN4tu8zEKkHtmDmc5cVvT39WKwWVlcUMzo8zltv/o6PPqwhHIoZddUh8o+I1E8ZqgUJA1TuOgC6PoZILbAVKGMZoesG7S1d+LyTfHSyhnM1ddOVQ7PQBnxn5I03Tjq2bk28bAmm6z0A9gIvY27HLDvmIQowgMj3gZ+hlJqvon7e1dGRV58HTYOXn/s/RL6NWfS17JiHbDsi30fkF4iohY4PLBg319RW4+nSQal24DRmBe0altGQxUAd8B3gKEoZ8UqJ4y4Uamqrqdx1AKXrA6Jpp4EsTEO23EWmIcyw8Xtit1ejlEqkbjq5AnFzXrswkwX/DKSkCGMR6AVeAo4A/RCZggkgadW84azDDsw6zMf44uqnJ4D3gZfRtBMoFUr27MPiD3mYxwHsGMYdwCHgIGY4ejPm9xBQDfwSkeNK10cdbjc/+fF3k/7Q0o/xPP40mBtVm1Hqy5jnIHaw9NMtQaABOAH8FpFPEfFiGAmr700hPE185gCIG7OA5DbMQpm1mEnCDMyyCuusdnXMJLkPM5XaDnwGnEXkLCLti1Hdm044irwpdUEpJ5APFKNUKSK3RDbgZ47iwRjQjUgX0AFcR2QcMBI5tJEs/h/GMBxGKn9DKwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyMC0wNC0xMlQyMDoyMDo0OSswMDowME0is3UAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjAtMDQtMTJUMjA6MjA6NDkrMDA6MDA8fwvJAAAARnRFWHRzb2Z0d2FyZQBJbWFnZU1hZ2ljayA2LjcuOC05IDIwMTQtMDUtMTIgUTE2IGh0dHA6Ly93d3cuaW1hZ2VtYWdpY2sub3Jn3IbtAAAAABh0RVh0VGh1bWI6OkRvY3VtZW50OjpQYWdlcwAxp/+7LwAAABh0RVh0VGh1bWI6OkltYWdlOjpoZWlnaHQAMTkyDwByhQAAABd0RVh0VGh1bWI6OkltYWdlOjpXaWR0aAAxOTLTrCEIAAAAGXRFWHRUaHVtYjo6TWltZXR5cGUAaW1hZ2UvcG5nP7JWTgAAABd0RVh0VGh1bWI6Ok1UaW1lADE1ODY3MjI4NDlV2OpiAAAAD3RFWHRUaHVtYjo6U2l6ZQAwQkKUoj7sAAAAVnRFWHRUaHVtYjo6VVJJAGZpbGU6Ly8vbW50bG9nL2Zhdmljb25zLzIwMjAtMDQtMTIvNTdhMDYyNGFhNzAyYzk3ZWU1YTE5MjgwYWEwNTkwZDMuaWNvLnBuZ1EXWHMAAAAASUVORK5CYII=</Image>

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


def json_indicators(request):
    p = SimpleViewPage(request, ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if not p.is_allowed():
        return redirect("{}:missing-rights".format(LinkDatabase.name))

    process_source_queue_size = BackgroundJobController.get_number_of_jobs(
        BackgroundJobController.JOB_PROCESS_SOURCE
    )

    sources = SourceOperationalData.objects.filter(
        consecutive_errors__gt=0, source_obj__enabled=True
    )

    error_jobs = BackgroundJobController.objects.filter(errors__gt=0)

    configuration_entry = Configuration.get_object().config_entry
    system_controller = SystemOperationController()

    if not request.user.is_authenticated:
        indicators = {}
        data = {"indicators": indicators}
        return JsonResponse(data, json_dumps_params={"indent": 4})

    sources_are_fetched = process_source_queue_size > 0
    sources_queue_size = process_source_queue_size
    is_sources_error = sources.count() > 0
    is_internet_ok = system_controller.is_internet_ok()

    is_threading_ok = system_controller.is_threading_ok()

    is_backgroundjobs_error = error_jobs.count() > 0
    is_configuration_error = False
    read_later_queue_size = ReadLater.objects.filter(user=request.user).count()
    read_later = read_later_queue_size > 0

    indicators = {}

    indicators["is_reading"] = {}
    indicators["is_reading"]["message"] = f"Sources queue:{sources_queue_size}"
    indicators["is_reading"]["status"] = sources_are_fetched

    indicators["read_later_queue"] = {}
    indicators["read_later_queue"][
        "message"
    ] = f"Read later queue {read_later_queue_size}"
    indicators["read_later_queue"]["status"] = read_later

    indicators["sources_error"] = {}
    indicators["sources_error"]["message"] = f"Sources error"
    indicators["sources_error"]["status"] = is_sources_error

    is_internet_error = (
        configuration_entry.enable_background_jobs and not is_internet_ok
    )
    indicators["internet_error"] = {}
    indicators["internet_error"]["message"] = f"Internet error"
    indicators["internet_error"]["status"] = is_internet_error

    is_remote_server_down = system_controller.is_remote_server_down()
    indicators["crawling_server_error"] = {}
    indicators["crawling_server_error"]["message"] = f"Crawling server error"
    indicators["crawling_server_error"]["status"] = is_remote_server_down

    threads_error = configuration_entry.enable_background_jobs and not is_threading_ok
    indicators["threads_error"] = {}
    indicators["threads_error"]["message"] = f"Threads error"
    indicators["threads_error"]["status"] = threads_error

    indicators["jobs_error"] = {}
    indicators["jobs_error"]["message"] = f"Jobs error"
    indicators["jobs_error"]["status"] = is_backgroundjobs_error

    indicators["configuration_error"] = {}
    indicators["configuration_error"]["message"] = f"Configuration error"
    indicators["configuration_error"]["status"] = is_configuration_error

    data = {"indicators": indicators}
    return JsonResponse(data, json_dumps_params={"indent": 4})


def get_menu(request):
    status_code = 200
    content_type = "text/html"
    text = ""

    p = ViewPage(request)
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)

    # even not logged users need to be able to see something

    if request.user.is_authenticated:
        p.context["is_read_later"] = (
            ReadLater.objects.filter(user=request.user).count() != 0
        )

    return p.render_implementation("base_menu.html")


def json_search_container(request):
    c = Configuration.get_object()

    data = {}

    rows = []

    search_icon = static("{}/icons/icons8-search-100.png".format(LinkDatabase.name))

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:search-engines")
    row["icon"] = search_icon
    row["title"] = "Search Internet"
    rows.append(row)

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:gateways")
    row["icon"] = search_icon
    row["title"] = "Gateways"
    rows.append(row)

    for searchview in SearchView.objects.filter(user=False):
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:entries") + "?view=" + str(searchview.id)
        row["icon"] = search_icon
        row["title"] = searchview.name
        rows.append(row)

    data["rows"] = rows
    data["title"] = "Search"

    return JsonResponse(data, json_dumps_params={"indent": 4})


def json_global_container(request):
    data = {}

    config_entry = ConfigurationEntry.get()

    rows = []

    tag_icon = static("{}/icons/icons8-tags-100.png".format(LinkDatabase.name))
    domains_icon = static("{}/icons/icons8-www-64.png".format(LinkDatabase.name))
    keywords_icon = static("{}/icons/icons8-letters-96.png".format(LinkDatabase.name))
    categories_icon = static("{}/icons/icons8-broadcast-100.png".format(LinkDatabase.name))
    sources_icon = static("{}/icons/icons8-broadcast-100.png".format(LinkDatabase.name))

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:tags-show-all")
    row["icon"] = tag_icon
    row["title"] = "Tags"
    rows.append(row)

    if config_entry.enable_domain_support:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:domains")
        row["icon"] = domains_icon
        row["title"] = "Domains"
        rows.append(row)

    if config_entry.enable_keyword_support:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:keywords")
        row["icon"] = keywords_icon
        row["title"] = "Keywords"
        rows.append(row)

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:categories-view")
    row["icon"] = categories_icon
    row["title"] = "Categories"
    rows.append(row)

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:sources")
    row["icon"] = sources_icon
    row["title"] = "Sources"
    rows.append(row)

    data["rows"] = rows
    data["title"] = "Global"

    return JsonResponse(data, json_dumps_params={"indent": 4})


def json_personal_container(request):
    data = {}

    read_later_icon = static("{}/icons/icons8-bookmarks-100.png".format(LinkDatabase.name))
    user_tags_icon = static("{}/icons/icons8-tags-100.png".format(LinkDatabase.name))
    user_browse_icon = static("{}/icons/icons8-link-90.png".format(LinkDatabase.name))
    user_search_icon = static("{}/icons/icons8-link-90.png".format(LinkDatabase.name))
    user_comments_icon = static("{}/icons/icons8-link-90.png".format(LinkDatabase.name))

    user_obj = UserConfig.get_or_create(request.user)
    if not user_obj.is_authenticated():
        return JsonResponse(data, json_dumps_params={"indent": 4})

    config_entry = ConfigurationEntry.get()

    rows = []

    read_later_queue_size = ReadLater.objects.filter(user=request.user).count()
    read_later = read_later_queue_size > 0

    if read_later:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:read-later-entries")
        row["icon"] = read_later_icon
        row["title"] = "Read later"
        rows.append(row)

    for searchview in SearchView.objects.filter(user=True):
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:entries") + "?view=" + str(searchview.id)
        row["icon"] = user_search_icon
        row["title"] = searchview.name
        rows.append(row)

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:user-tags-show")
    row["icon"] = user_tags_icon
    row["title"] = "Tags"
    rows.append(row)

    if config_entry.track_user_navigation:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:user-browse-history")
        row["icon"] = user_browse_icon
        row["title"] = "Browse history"
        rows.append(row)

    if config_entry.track_user_searches:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:user-search-history")
        row["icon"] = user_search_icon
        row["title"] = "Search history"
        rows.append(row)

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:user-comments")
    row["icon"] = user_comments_icon
    row["title"] = "Comments"
    rows.append(row)

    data["rows"] = rows
    data["title"] = "Personal"

    return JsonResponse(data, json_dumps_params={"indent": 4})


def json_tools_container(request):
    data = {}

    add_icon = static("{}/icons/icons8-add-link-96.png".format(LinkDatabase.name))
    download_url_icon = static("{}/icons/icons8-download-page-96.png".format(LinkDatabase.name))
    download_music_url_icon = static("{}/icons/icons8-download-music-96.png".format(LinkDatabase.name))
    download_video_url_icon = static("{}/icons/icons8-download-video-96.png".format(LinkDatabase.name))
    radar_icon = static("{}/icons/icons8-radar-64.png".format(LinkDatabase.name))

    user_obj = UserConfig.get_or_create(request.user)
    if not user_obj.is_authenticated():
        return JsonResponse(data, json_dumps_params={"indent": 4})

    rows = []

    if user_obj.can_add():
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:entry-add-simple")
        row["icon"] = add_icon
        row["title"] = "Add entry"
        rows.append(row)

    if user_obj.can_download():
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:download-url")
        row["icon"] = download_url_icon
        row["title"] = "Downloads URL"
        rows.append(row)

        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:download-music-url")
        row["icon"] = download_music_url_icon
        row["title"] = "Downloads music"
        rows.append(row)

        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:download-video-url")
        row["icon"] = download_video_url_icon
        row["title"] = "Downloads video"
        rows.append(row)

    if user_obj.user.is_staff:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:page-scan-link")
        row["icon"] = radar_icon
        row["title"] = "Scan page URL"
        rows.append(row)

    if user_obj.user.is_staff:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:page-show-props")
        row["icon"] = radar_icon
        row["title"] = "Page Properties"
        rows.append(row)

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:is-url-allowed")
    row["icon"] = radar_icon
    row["title"] = "Check link for robots.txt"
    rows.append(row)

    if user_obj.user.is_staff:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:page-verify")
        row["icon"] = radar_icon
        row["title"] = "Verify page"
        rows.append(row)

    row = {}
    row["link"] = reverse(f"{LinkDatabase.name}:cleanup-link")
    row["icon"] = radar_icon
    row["title"] = "Cleanup Link"
    rows.append(row)

    data["rows"] = rows
    data["title"] = "Tools"

    return JsonResponse(data, json_dumps_params={"indent": 4})


def json_users_container(request):
    data = {}

    user_obj = UserConfig.get_or_create(request.user)

    login_icon = static("{}/icons/icons8-login-100.png".format(LinkDatabase.name))
    configuration_icon = static("{}/icons/icons8-configuration-67.png".format(LinkDatabase.name))
    accounts_icon = static("{}/icons/account.png".format(LinkDatabase.name))
    logout_icon = static("{}/icons/icons8-logout-100.png".format(LinkDatabase.name))

    rows = []

    if not user_obj.is_authenticated():
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:login") + "?next=" + reverse(f"{LinkDatabase.name}:index")
        row["icon"] = login_icon
        row["title"] = "Login"
        rows.append(row)
    else:
        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:admin-page")
        row["icon"] = configuration_icon
        row["title"] = "Admin"
        rows.append(row)

        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:user-config")
        row["icon"] = accounts_icon
        row["title"] = "Admin"
        rows.append(row)

        row = {}
        row["link"] = reverse(f"{LinkDatabase.name}:logout") + "?next=" + reverse(f"{LinkDatabase.name}:index")
        row["icon"] = logout_icon
        row["title"] = "Logout"
        rows.append(row)

    data["rows"] = rows
    data["title"] = "User"

    return JsonResponse(data, json_dumps_params={"indent": 4})
