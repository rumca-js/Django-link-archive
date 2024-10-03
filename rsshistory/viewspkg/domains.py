from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlencode

from ..apps import LinkDatabase
from ..models import Domains, ConfigurationEntry
from ..controllers import (
    EntryWrapper,
    EntryDataBuilder,
    LinkDataController,
    DomainsController,
)
from ..views import ViewPage
from ..forms import DomainsChoiceForm, DomainEditForm, LinkInputForm
from ..queryfilters import DomainFilter


class DomainsListView(generic.ListView):
    model = DomainsController
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super().get(*args, **kwargs)

    def get_queryset(self):
        self.sort = "normal"
        if "sort" in self.request.GET:
            sort = self.request.GET["sort"]
            if sort.strip() != "":
                self.sort = sort

        self.query_filter = DomainFilter(self.request.GET)

        objects = self.query_filter.get_filtered_objects()

        if self.sort != "normal":
            return objects.order_by("-" + self.sort)
        return objects

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        self.init_display_type(context)

        context["sort"] = self.sort

        self.filter_form = self.get_form()
        self.filter_form.method = "GET"
        self.filter_form.action_url = self.get_form_action_link()

        context["form"] = self.filter_form
        context["query_filter"] = self.query_filter
        context["reset_link"] = self.get_reset_link()

        return context

    def get_form(self):
        return DomainsChoiceForm(self.request.GET)

    def get_reset_link(self):
        return reverse("{}:domains".format(LinkDatabase.name))

    def get_form_action_link(self):
        return reverse("{}:domains".format(LinkDatabase.name))

    def init_display_type(self, context):
        # TODO https://stackoverflow.com/questions/57487336/change-value-for-paginate-by-on-the-fly
        # if type is not normal, no pagination
        if "type" in self.request.GET:
            context["type"] = self.request.GET["type"]
        else:
            context["type"] = "normal"
        context["args"] = self.get_args()

    def get_args(self):
        arg_data = {}
        for arg in self.request.GET:
            if arg != "type":
                arg_data[arg] = self.request.GET[arg]

        return "&" + urlencode(arg_data)


class DomainsDetailView(generic.DetailView):
    model = DomainsController
    context_object_name = "domain_detail"

    def get(self, *args, **kwargs):
        """
        API: Used to redirect if user does not have rights
        """

        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        view = super().get(*args, **kwargs)
        return view

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        context["page_title"] += " {} domain".format(self.object.domain)

        return context


class DomainsByNameDetailView(generic.DetailView):
    model = DomainsController
    context_object_name = "domain_detail"

    def get(self, *args, **kwargs):
        """
        API: Used to redirect if user does not have rights
        """

        p = ViewPage(self.request)
        data = p.check_access()
        if data is not None:
            return redirect("{}:missing-rights".format(LinkDatabase.name))

        view = super().get(*args, **kwargs)
        return view

    def get_object(self):
        domain_name = self.request.GET["domain_name"]
        self.objects = DomainsController.objects.filter(domain=domain_name)
        if self.objects.count() > 0:
            self.object = self.objects[0]
            return self.object
        else:
            if domain_name.find("http") == -1:
                domain_name = "https://" + domain_name

            entries = LinkDataController.objects.filter(link=domain_name)
            if len(entries) > 0:
                entry = entries[0]
                if not entry.dead:
                    id = DomainsController.add(entry.link)
                    self.object = DomainsController.objects.get(id)
                    return self.object

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        if self.object and self.object.domain:
            context["page_title"] += " {} domain".format(self.object.domain)

        return context


def domain_edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit domain")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    domains = DomainsController.objects.filter(id=pk)
    if not domains.exists():
        p.context["summary_text"] = "Could not find such domain"
        return p.render("summary_present.html")

    domain = domains[0]

    if request.method == "POST":
        form = DomainEditForm(request.POST, instance=domain)
        p.context["form"] = form

        if form.is_valid():
            domain = form.save()

            return HttpResponseRedirect(domain.get_absolute_url())

        p.context["summary_text"] = "Could not edit domain {}".format(form.cleaned_data)
        return p.render("summary_present.html")
    else:
        form = DomainEditForm(instance=domain)

        form.method = "POST"
        form.action_url = reverse("{}:domain-edit".format(LinkDatabase.name), args=[pk])
        p.context["form"] = form
        return p.render("form_basic.html")


def domain_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove domain")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    domain = DomainsController.objects.get(id=pk)
    domain.delete()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domains_remove_all(request):
    p = ViewPage(request)
    p.set_title("Remove all domains")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    DomainsController.remove_all()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domain_update_data(request, pk):
    p = ViewPage(request)
    p.set_title("Update domain data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    domains = DomainsController.objects.filter(id=pk)
    domain = domains[0]
    domain.update_object(force=True)

    return HttpResponseRedirect(
        reverse(
            "{}:domain-detail".format(LinkDatabase.name),
            kwargs={"pk": domain.id},
        )
    )


def domains_fix(request):
    p = ViewPage(request)
    p.set_title("Fix domains")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    DomainsController.update_all()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domains_read_bookmarks(request):
    p = ViewPage(request)
    p.set_title("Read domains from bookmarks")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    EntryDataBuilder().read_domains_from_bookmarks()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domain_json(request, pk):
    domains = DomainsController.objects.filter(id=pk)

    if domains.count() == 0:
        p = ViewPage(request)
        p.set_title("Domain json")
        p.context["summary_text"] = "No such domain in the database {}".format(pk)
        return p.render("summary_present.html")

    domain = domains[0]

    # JsonResponse
    return JsonResponse(domain.get_map())


def domains_json(request):
    from ..queryfilters import DomainFilter

    domains = DomainsController.objects.all()

    page_limit = "standard"
    if "page_limit" in request.GET:
        page_limit = request.GET["page_limit"]

    # Data
    query_filter = DomainFilter(request.GET)
    if page_limit != "no-limit":
        query_filter.use_page_limit = True
    domains = query_filter.get_filtered_objects()

    from ..serializers.domainexporter import DomainJsonExporter

    exp = DomainJsonExporter()

    # JsonResponse
    return JsonResponse(exp.get_json(domains))


def domains_reset_dynamic_data(request):
    p = ViewPage(request)
    p.set_title("Reset dynamic data")

    DomainsController.reset_dynamic_data()

    return redirect("{}:domains".format(LinkDatabase.name))
