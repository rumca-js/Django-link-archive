from pathlib import Path
import logging

from django.views import generic
from django.urls import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..apps import LinkDatabase
from ..models import (
    LinkTagsDataModel,
    ConfigurationEntry,
    UserConfig,
    BackgroundJob,
    PersistentInfo,
    SourceExportHistory,
    Domains,
)
from ..controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
)
from ..configuration import Configuration
from ..forms import ConfigForm, UserConfigForm, BackgroundJobForm
from ..views import ViewPage


def admin_page(request):
    p = ViewPage(request)
    p.set_title("Admin")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data
    return p.render("admin_page.html")


def configuration_page(request):
    p = ViewPage(request)
    p.set_title("Configuration")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

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
    form.action_url = reverse("{}:configuration".format(LinkDatabase.name))

    p.set_variable("config_form", form)

    return p.render("configuration.html")


def system_status(request):
    p = ViewPage(request)
    p.set_title("Status")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

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


def missing_rights(request):
    p = ViewPage(request)
    p.set_title("Missing rights")
    p.context["summary_text"] = "user information is not valid, cannot save"
    return p.render("summary_present.html")


def user_config(request):
    p = ViewPage(request)
    p.set_title("User configuration")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

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
    form.action_url = reverse("{}:user-config".format(LinkDatabase.name))

    p.context["config_form"] = form
    p.context["user_object"] = user_obj

    return p.render("user_configuration.html")


class BackgroundJobsView(generic.ListView):
    model = BackgroundJob
    context_object_name = "content_list"

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
            BackgroundJob.objects.create(**form.cleaned_data)

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


def backgroundjob_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove a new background job")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    bg = BackgroundJob.objects.get(id=pk)
    bg.delete()

    return HttpResponseRedirect(
        reverse("{}:backgroundjobs".format(LinkDatabase.name))
    )


def backgroundjobs_remove_all(request):
    p = ViewPage(request)
    p.set_title("Remove all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    bg = BackgroundJob.objects.all()
    bg.delete()

    return HttpResponseRedirect(
        reverse("{}:backgroundjobs".format(LinkDatabase.name))
    )


def backgroundjobs_check_new(request):
    p = ViewPage(request)
    p.set_title("Check for new background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..threadhandlers import RefreshThreadHandler

    refresh_handler = RefreshThreadHandler()
    refresh_handler.refresh()

    return HttpResponseRedirect(
        reverse("{}:backgroundjobs".format(LinkDatabase.name))
    )


def backgroundjobs_perform_all(request):
    p = ViewPage(request)
    p.set_title("Process all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..threadhandlers import HandlerManager, RefreshThreadHandler

    mgr = HandlerManager()
    mgr.process_all()

    return HttpResponseRedirect(
        reverse("{}:backgroundjobs".format(LinkDatabase.name))
    )


def backgroundjobs_remove(request, job_type):
    p = ViewPage(request)
    p.set_title("Remove background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJob.objects.filter(job=job_type)
    jobs.delete()

    return HttpResponseRedirect(
        reverse("{}:backgroundjobs".format(LinkDatabase.name))
    )


class PersistentInfoView(generic.ListView):
    model = PersistentInfo
    context_object_name = "content_list"

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(PersistentInfoView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(PersistentInfoView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        return context


def truncate_log_all(request):
    p = ViewPage(request)
    p.set_title("Clearing all logs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    PersistentInfo.truncate()

    return HttpResponseRedirect(reverse("{}:logs".format(LinkDatabase.name)))


def truncate_log(request):
    p = ViewPage(request)
    p.set_title("Clearing info logs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    PersistentInfo.objects.filter(level__lt=40).delete()

    return HttpResponseRedirect(reverse("{}:logs".format(LinkDatabase.name)))


def truncate_log_errors(request):
    p = ViewPage(request)
    p.set_title("Clearing error logs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    PersistentInfo.objects.filter(level=logging.ERROR).delete()

    return HttpResponseRedirect(reverse("{}:logs".format(LinkDatabase.name)))
