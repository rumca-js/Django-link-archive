from pathlib import Path
import logging

from django.views import generic
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..models import (
    LinkTagsDataModel,
    ConfigurationEntry,
    UserConfig,
    BackgroundJob,
    PersistentInfo,
    SourceExportHistory,
    Domains,
)
from ..configuration import Configuration
from ..forms import ConfigForm, UserConfigForm, BackgroundJobForm
from ..controllers import (
    BackgroundJobController,
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
)
from ..views import ContextData, ViewPage


def admin_page(request):
    p = ViewPage(request)
    p.set_title("Admin")
    p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    return p.render("admin_page.html")


def configuration_page(request):
    p = ViewPage(request)
    p.set_title("Configuration")
    p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)

    ob = ConfigurationEntry.get()

    if request.method == "POST":
        form = ConfigForm(request.POST, instance=ob)
        if form.is_valid():
            form.save()
        else:
            p.set_variable("summary_text", "Form is invalid")
            return p.render("summary_present.html")

    ob = ConfigurationEntry.get()
    form = ConfigForm(instance=ob)

    form.method = "POST"
    form.action_url = reverse("{}:configuration".format(ContextData.app_name))

    p.set_variable("config_form", form)

    return p.render("configuration.html")


def system_status(request):
    p = ViewPage(request)
    p.set_title("Status")
    p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)

    c = Configuration.get_object()
    p.context["directory"] = c.directory

    p.context["SourceDataModel"] = SourceDataController.objects.count()
    p.context["LinkDataModel"] = LinkDataController.objects.count()
    p.context["ArchiveLinkDataModel"] = ArchiveLinkDataController.objects.count()
    p.context["LinkTagsDataModel"] = LinkTagsDataModel.objects.count()
    p.context["ConfigurationEntry"] = ConfigurationEntry.objects.count()
    p.context["UserConfig"] = UserConfig.objects.count()
    p.context["BackgroundJob"] = BackgroundJob.objects.count()

    from ..dateutils import DateUtils

    p.context["Current_DateTime"] = DateUtils.get_datetime_now_utc()

    p.context["ServerLogLength"] = PersistentInfo.objects.count()
    p.context["DomainsLength"] = Domains.objects.count()

    p.context["server_path"] = Path(".").resolve()
    p.context["directory"] = Path(".").resolve()

    history = SourceExportHistory.get_safe()
    p.context["export_history_list"] = history

    return p.render("system_status.html")


def about(request):
    p = ViewPage(request)
    p.set_title("About")
    return p.render("about.html")


def user_config(request):
    p = ViewPage(request)
    p.set_title("User configuration")
    p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)

    user_name = request.user.get_username()

    user_obj = UserConfig.get_or_create(user_name)

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
    form.action_url = reverse("{}:user-config".format(ContextData.app_name))

    p.context["config_form"] = form
    p.context["user_object"] = user_obj

    return p.render("user_configuration.html")


class BackgroundJobsView(generic.ListView):
    model = BackgroundJob
    context_object_name = "content_list"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BackgroundJobsView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        context["BackgroundJob"] = BackgroundJob.objects.count()

        return context


def backgroundjob_add(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Add a new background job"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = BackgroundJobForm(request.POST)
        if form.is_valid():
            BackgroundJob.objects.create(**form.cleaned_data)

            return HttpResponseRedirect(
                reverse("{}:backgroundjobs".format(ContextData.app_name))
            )
        else:
            context["summary_text"] = "Form is invalid"
            return ContextData.render(request, "summary_present.html", context)

    form = BackgroundJobForm()

    form.method = "POST"
    form.action_url = reverse("{}:backgroundjob-add".format(ContextData.app_name))

    context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


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


def backgroundjobs_check_new(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Background check if new"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    from ..threadhandlers import RefreshThreadHandler

    refresh_handler = RefreshThreadHandler()
    refresh_handler.refresh()

    return HttpResponseRedirect(
        reverse("{}:backgroundjobs".format(ContextData.app_name))
    )


def backgroundjobs_perform_all(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Background perform all"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    from ..threadhandlers import HandlerManager, RefreshThreadHandler

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
    context_object_name = "content_list"

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

    PersistentInfo.objects.filter(level__lt=40).truncate()

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
