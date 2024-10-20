from django.views import generic
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.db.models import Q

from ..apps import LinkDatabase
from ..models import (
    ConfigurationEntry,
    BackgroundJob,
    LinkDataModel,
)
from ..controllers import (
    BackgroundJobController,
)
from ..forms import (
    BackgroundJobForm,
)
from ..views import ViewPage, GenericListView


def backgroundjobs(request):
    p = ViewPage(request)
    p.set_title("Jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    return p.render("backgroundjob_list.html")


class BackgroundJobsView(GenericListView):
    model = BackgroundJobController
    context_object_name = "content_list"
    paginate_by = 500
    template_name = str(ViewPage.get_full_template("backgroundjob_list__element.html"))

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(BackgroundJobsView, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(BackgroundJobsView, self).get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        context["BackgroundJob"] = BackgroundJob.objects.count()
        context["page_title"] += " " + self.get_title()

        return context

    def get_title(self):
        return "Jobs"


def backgroundjob_add(request):
    p = ViewPage(request)
    p.set_title("Add a new background job")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = BackgroundJobForm(request.POST)
        if form.is_valid():
            job = form.cleaned_data["job"]
            themap = form.cleaned_data

            themap["priority"] = BackgroundJobController.get_job_priority(job)

            BackgroundJobController.objects.create(**themap)

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

    from ..threadhandlers import RefreshProcessor

    refresh_handler = RefreshProcessor()
    refresh_handler.run()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_perform_all(request):
    p = ViewPage(request)
    p.set_title("Process all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..threadhandlers import GenericJobsProcessor

    mgr = GenericJobsProcessor()
    mgr.run()

    return HttpResponseRedirect(reverse("{}:backgroundjobs".format(LinkDatabase.name)))


def backgroundjobs_enable_all(request):
    p = ViewPage(request)
    p.set_title("Enables all background jobs")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    jobs = BackgroundJobController.objects.all()
    for job in jobs:
        job.enable()

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


def is_entry_download(request, pk):
    """
    User might set access through config. Default is all
    """
    p = ViewPage(request)
    p.set_title("JSON entries")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    is_downloaded = False

    entries = LinkDataModel.objects.filter(id = pk)

    if entries.exists():
        job_condition = (Q(job=BackgroundJobController.JOB_DOWNLOAD_FILE) |
            Q(job=BackgroundJobController.JOB_LINK_DOWNLOAD_MUSIC) |
            Q(job=BackgroundJobController.JOB_LINK_DOWNLOAD_VIDEO))

        job_condition &= Q(subject = entry.link)
        job_condition &= Q(enabled = True)

        entry = entries[0]

        jobs = BackgroundJobController.objects.filter(job_condition)
        if jobs.exists():
            is_downloaded = True

    json_obj = {"status" : is_downloaded }

    return JsonResponse(json_obj)
