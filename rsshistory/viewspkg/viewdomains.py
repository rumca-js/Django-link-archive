from django.views import generic
from django.urls import reverse

from ..models import Domains
from ..views import ContextData
from ..controllers import (
    LinkDataController,
    LinkDataHyperController,
)


class DomainsListView(generic.ListView):
    model = Domains
    context_object_name = "domain_list"
    paginate_by = 100

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(DomainsListView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        # TODO https://stackoverflow.com/questions/57487336/change-value-for-paginate-by-on-the-fly
        # if type is not normal, no pagination
        if "type" in self.request.GET:
            context["type"] = self.request.GET["type"]
        else:
            context["type"] = "normal"

        return context


def domain_remove(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domain remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    domain = Domains.objects.get(id=pk)
    domain.delete()

    context["summary_text"] = "Domain was removed"

    return ContextData.render(request, "summary_present.html", context)


def domains_remove_all(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domains remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    domains = Domains.objects.all()
    domains.delete()

    context["summary_text"] = "Domains were removed"

    return ContextData.render(request, "summary_present.html", context)


def domains_fix(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domain fix"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    Domains.fix_domain_objs()

    context["summary_text"] = "Domains were fixed"

    return ContextData.render(request, "summary_present.html", context)


def domains_read_bookmarks(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domain read bookmarks"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    LinkDataHyperController.read_domains_from_bookmarks()

    context["summary_text"] = "Domains were read from bookmarks"

    return ContextData.render(request, "summary_present.html", context)


