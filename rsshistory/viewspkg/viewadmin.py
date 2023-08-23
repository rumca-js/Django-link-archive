from pathlib import Path
import logging

from django.views import generic
from django.urls import reverse

from ..models import (
    LinkTagsDataModel,
    ConfigurationEntry,
    UserConfig,
    BackgroundJob,
    PersistentInfo,
    RssSourceExportHistory,
    Domains,
)
from ..configuration import Configuration
from ..forms import ConfigForm, UserConfigForm
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
)
from ..views import ContextData


def admin_page(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Admin page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    return ContextData.render(request, "admin_page.html", context)


def configuration_page(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Configuration page"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    ob = ConfigurationEntry.get()

    if request.method == "POST":
        form = ConfigForm(request.POST, instance=ob)
        if form.is_valid():
            form.save()
        else:
            context["summary_text"] = "Form is invalid"
            return ContextData.render(request, "summary_present.html", context)

    ob = ConfigurationEntry.get()
    form = ConfigForm(instance=ob)

    form.method = "POST"
    form.action_url = reverse("{}:configuration".format(ContextData.app_name))

    context["config_form"] = form

    return ContextData.render(request, "configuration.html", context)


def system_status(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Status"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    c = Configuration.get_object()
    context["directory"] = c.directory

    context["SourceDataModel"] = len(SourceDataController.objects.all())
    # Takes too long context["LinkDataModel"] = len(LinkDataController.objects.all())
    context["LinkTagsDataModel"] = len(LinkTagsDataModel.objects.all())
    context["ConfigurationEntry"] = len(ConfigurationEntry.objects.all())
    context["UserConfig"] = len(UserConfig.objects.all())
    context["BackgroundJob"] = len(BackgroundJob.objects.all())

    from ..dateutils import DateUtils

    context["Current_DateTime"] = DateUtils.get_datetime_now_utc()

    context["ServerLogLength"] = len(PersistentInfo.objects.all())
    # Takes too long context["ServerLogErrorsLength"] = len(PersistentInfo.objects.filter(level = logging.ERROR))
    context["DomainsLength"] = len(Domains.objects.all())

    context["server_path"] = Path(".").resolve()
    context["directory"] = Path(".").resolve()

    # Takes too long history = RssSourceExportHistory.get_safe()
    # Takes too long context["export_history_list"] = history

    return ContextData.render(request, "system_status.html", context)


def about(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - About"

    return ContextData.render(request, "about.html", context)


def user_config(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - User configuration"

    if not request.user.is_authenticated:
        return ContextData.render(request, "missing_rights.html", context)

    user_name = request.user.get_username()

    obs = UserConfig.objects.filter(user=user_name)
    if not obs.exists():
        rec = UserConfig(user=user_name)
        rec.save()

    obs = UserConfig.objects.filter(user=user_name)

    if len(obs) > 0:
        for key, value in enumerate(obs):
            if key != 0:
                value.truncate()

    ob = obs[0]

    if request.method == "POST":
        form = UserConfigForm(request.POST, instance=ob)
        if form.is_valid():
            form.save()
        else:
            context["summary_text"] = "user information is not valid, cannot save"
            return ContextData.render(request, "summary_present.html", context)

        obs = UserConfig.objects.filter(user=user_name)
    else:
        form = UserConfigForm(instance=ob)

    form.method = "POST"
    form.action_url = reverse("{}:user-config".format(ContextData.app_name))

    context["config_form"] = form
    context["user_object"] = ob

    return ContextData.render(request, "user_configuration.html", context)




class BackgroundJobsView(generic.ListView):
    model = BackgroundJob
    context_object_name = "jobs_list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BackgroundJobsView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        context["BackgroundJob"] = len(BackgroundJob.objects.all())

        return context


def backgroundjob_remove(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Background job remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    bg = BackgroundJob.objects.get(id=pk)
    bg.delete()

    context["summary_text"] = "Background job has been removed"
    return ContextData.render(request, "summary_present.html", context)


def backgroundjobs_remove_all(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Remove all background jobs"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    bg = BackgroundJob.objects.all()
    bg.delete()

    context["summary_text"] = "Background jobs were removed"
    return ContextData.render(request, "summary_present.html", context)


def backgroundjobs_perform_all(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Background perform all"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    from ..threadhandlers import HandlerManager, RefreshThreadHandler
    refresh_handler = RefreshThreadHandler()
    refresh_handler.refresh()

    mgr = HandlerManager()
    mgr.process_all()

    context["summary_text"] = "Background jobs have been processed"

    return ContextData.render(request, "summary_present.html", context)


def backgroundjobs_remove(request, job_type):
    context = ContextData.get_context(request)
    context["page_title"] += " - Background jobs remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    jobs = BackgroundJob.objects.filter(job=job_type)
    jobs.delete()

    context["summary_text"] = "Background jobs has been removed"

    return ContextData.render(request, "summary_present.html", context)


class PersistentInfoView(generic.ListView):
    model = PersistentInfo
    context_object_name = "info_list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(PersistentInfoView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        return context


def truncate_log_all(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - clearing logs"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    PersistentInfo.truncate()

    context["summary_text"] = "Clearing errors done"

    return ContextData.render(request, "summary_present.html", context)


def truncate_log(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - clearing logs"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    PersistentInfo.objects.filter(level__lt = 40).truncate()

    context["summary_text"] = "Clearing errors done"

    return ContextData.render(request, "summary_present.html", context)


def truncate_log_errors(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - clearing log errors"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    PersistentInfo.objects.filter(level=logging.ERROR).truncate()

    context["summary_text"] = "Clearing errors done"

    return ContextData.render(request, "summary_present.html", context)
