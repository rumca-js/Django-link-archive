from django.views import generic
from django.urls import reverse
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..models import Domains
from ..views import ContextData
from ..controllers import (
    LinkDataController,
    LinkDataHyperController,
)
from ..forms import DomainsChoiceForm, LinkInputForm
from ..queryfilters import DomainFilter


class DomainsListView(generic.ListView):
    model = Domains
    context_object_name = "content_list"
    paginate_by = 100

    def get_queryset(self):
        self.query_filter = DomainFilter(self.request.GET)
        return self.query_filter.get_filtered_objects()

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

        self.filter_form = self.get_form()
        self.filter_form.method = "GET"
        self.filter_form.action_url = self.get_form_action_link()

        context["filter_form"] = self.filter_form
        context["query_filter"] = self.query_filter

        return context

    def get_form(self):
        return DomainsChoiceForm(self.request.GET)

    def get_form_action_link(self):
        return reverse("{}:domains".format(ContextData.app_name))


class DomainsDetailView(generic.DetailView):
    model = Domains
    context_object_name = "domain_detail"

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super(DomainsDetailView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        context["page_title"] += " {} domain".format(self.object.domain)

        return context


class DomainsByNameDetailView(generic.DetailView):
    model = Domains
    context_object_name = "domain_detail"

    def get_object(self):
        domain_name = self.request.GET["domain_name"]
        self.objects = Domains.objects.filter(domain = domain_name)
        if self.objects.count() > 0:
            self.object = self.objects[0]
            return self.object

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super(DomainsByNameDetailView, self).get_context_data(**kwargs)
        context = ContextData.init_context(self.request, context)

        context["page_title"] += " {} domain".format(self.object.domain)

        return context


def domain_add(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - add domain"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = LinkInputForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data["link"]

            domain = Domains.add(link)

            return HttpResponseRedirect(
                reverse(
                    "{}:domain-detail".format(ContextData.app_name),
                    kwargs={"pk": domain.id},
                )
            )
        else:
            context["summary_text"] = "Form is invalid"
            return ContextData.render(request, "summary_present.html", context)

    else:
        form = LinkInputForm()
        form.method = "POST"

        context["form_title"] = "Add new domain"
        context["form"] = form

    return ContextData.render(request, "form_basic.html", context)


def domain_remove(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domain remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    domains = Domains.objects.get(id=pk)
    if domains.count() == 0:
        context["summary_text"] = "Domain does not exist"
        return ContextData.render(request, "summary_present.html", context)

    domain.delete()

    return HttpResponseRedirect(
        reverse("{}:domains".format(ContextData.app_name))
    )


def domains_remove_all(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domains remove"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    Domains.remove_all()

    return HttpResponseRedirect(
        reverse("{}:domains".format(ContextData.app_name))
    )


def domain_update_data(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domain update data"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    domains = Domains.objects.filter(id=pk)
    domain = domains[0]
    domain.update_object(force=True)

    return HttpResponseRedirect(
        reverse(
            "{}:domain-detail".format(ContextData.app_name),
            kwargs={"pk": domain.id},
        )
    )

    return ContextData.render(request, "summary_present.html", context)


def domains_fix(request):
    context = ContextData.get_context(request)
    context["page_title"] += " - Domain fix"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    Domains.fix_all()

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


def domain_json(request, pk):
    domains = Domains.objects.filter(id=pk)

    if domains.count() == 0:
        context["summary_text"] = "No such domain in the database {}".format(pk)
        return ContextData.render(request, "summary_present.html", context)

    domain = domains[0]

    # JsonResponse
    return JsonResponse(domain.get_map())


def domains_json(request):
    from ..queryfilters import DomainFilter

    domains = Domains.objects.all()

    # Data
    query_filter = DomainFilter(request.GET)
    query_filter.use_page_limit = True
    domains = query_filter.get_filtered_objects()

    from ..serializers.domainexporter import DomainJsonExporter

    exp = DomainJsonExporter()

    # JsonResponse
    return JsonResponse(exp.get_json(domains))
