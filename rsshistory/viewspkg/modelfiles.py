from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..models import ModelFiles
from ..views import ViewPage


class ModelFilesListView(generic.ListView):
    model = ModelFiles
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        sum_size_bytes = 0

        modelfiles = self.get_queryset()
        for modelfile in modelfiles:
            sum_size_bytes += modelfile.get_size_bytes()

        context["sum_size_bytes"] = sum_size_bytes
        context["sum_size_kilobytes"] = sum_size_bytes / 1000.0
        context["sum_size_megabytes"] = sum_size_bytes / 1000000.0

        return context


def model_file(request, pk):
    from ..forms import ImportSourceRangeFromInternetArchiveForm

    p = ViewPage(request)
    p.set_title("Model file")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    model_files = ModelFiles.objects.filter(id = pk)
    if model_files.exists():
        data = model_files[0].contents

        return HttpResponse(data, content_type='application/octet-stream')


def model_file_remove(request, pk):
    from ..forms import ImportSourceRangeFromInternetArchiveForm

    p = ViewPage(request)
    p.set_title("Remove model file")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    model_files = ModelFiles.objects.filter(id = pk)
    if model_files.exists():
        model_files.delete()

        return redirect("{}:model-files".format(LinkDatabase.name))
    else:
        p.context["summary_text"] = "Cannot find such model file"
        return p.render("summary_present.html")


def model_files_remove(request):
    from ..forms import ImportSourceRangeFromInternetArchiveForm

    p = ViewPage(request)
    p.set_title("Remove model file")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    ModelFiles.objects.all().delete()
    return redirect("{}:model-files".format(LinkDatabase.name))
