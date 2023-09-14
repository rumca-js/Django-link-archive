from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..apps import LinkDatabase
from ..models import Domains, DomainCategories, DomainSubCategories, ConfigurationEntry
from ..controllers import (
    LinkDataHyperController,
)
from ..views import ViewPage
from ..forms import DomainsChoiceForm, DomainEditForm, LinkInputForm
from ..queryfilters import DomainFilter


class DomainsListView(generic.ListView):
    model = Domains
    context_object_name = "content_list"
    paginate_by = 100

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(DomainsListView, self).get(*args, **kwargs)

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
        context = super(DomainsListView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        self.init_display_type(context)

        context["sort"] = self.sort

        self.filter_form = self.get_form()
        self.filter_form.method = "GET"
        self.filter_form.action_url = self.get_form_action_link()

        context["filter_form"] = self.filter_form
        context["query_filter"] = self.query_filter

        items = set()
        for cat in DomainCategories.objects.all():
            items.add(cat.category)
        items = sorted(list(items))
        context["categories"] = ",".join(items)
        items = set()
        for cat in DomainSubCategories.objects.all():
            items.add(cat.subcategory)
        items = sorted(list(items))
        context["subcategories"] = ",".join(items)

        return context

    def get_form(self):
        return DomainsChoiceForm(self.request.GET)

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
        thelist = ""
        for arg in self.request.GET:
            if arg != "type":
                thelist += "&{}={}".format(arg,self.request.GET[arg])
        return thelist



class DomainsDetailView(generic.DetailView):
    model = Domains
    context_object_name = "domain_detail"

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super(DomainsDetailView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        context["page_title"] += " {} domain".format(self.object.domain)

        return context


class DomainsByNameDetailView(generic.DetailView):
    model = Domains
    context_object_name = "domain_detail"

    def get_object(self):
        domain_name = self.request.GET["domain_name"]
        self.objects = Domains.objects.filter(domain=domain_name)
        if self.objects.count() > 0:
            self.object = self.objects[0]
            return self.object

    def get_context_data(self, **kwargs):
        from ..pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        # Call the base implementation first to get the context
        context = super(DomainsByNameDetailView, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        context["page_title"] += " {} domain".format(self.object.domain)

        return context


def domain_add(request):
    p = ViewPage(request)
    p.set_title("Add domain")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = LinkInputForm(request.POST)
        if form.is_valid():
            link = form.cleaned_data["link"]

            domain = Domains.add(link)

            return HttpResponseRedirect(
                reverse(
                    "{}:domain-detail".format(LinkDatabase.name),
                    kwargs={"pk": domain.id},
                )
            )
        else:
            p.context["summary_text"] = "Form is invalid"
            return p.render("summary_present.html")

    else:
        form = LinkInputForm()
        form.method = "POST"

        p.context["form_title"] = "Add new domain"
        p.context["form"] = form

    return p.render("form_basic.html")


def domain_edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit domain")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    domains = Domains.objects.filter(id=pk)
    if not domains.exists():
        p.context["summary_text"] = "Could not find such domain"
        return p.render("summary_present.html")

    domain = domains[0]

    if request.method == "POST":
        form = DomainEditForm(request.POST, instance=domain)
        p.context["form"] = form

        if form.is_valid():
            domain = form.save()
            category = domain.category
            subcategory = domain.subcategory

            DomainCategories.add(category)
            DomainSubCategories.add(category, subcategory)
            print("Category:{} subcategory:{}".format(category, subcategory))

            return HttpResponseRedirect(domain.get_absolute_url())

        p.context["summary_text"] = "Could not edit domain {}".format(form.cleaned_data)
        return p.render("summary_present.html")
    else:
        form = DomainEditForm(instance=domain)

        form.method = "POST"
        form.action_url = reverse(
            "{}:domain-edit".format(LinkDatabase.name), args=[pk]
        )
        p.context["form"] = form
        return p.render("form_basic.html")


def domain_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove domain")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    domain = Domains.objects.get(id=pk)
    domain.delete()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domains_remove_all(request):
    p = ViewPage(request)
    p.set_title("Remove all domains")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    Domains.remove_all()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domain_update_data(request, pk):
    p = ViewPage(request)
    p.set_title("Update domain data")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    domains = Domains.objects.filter(id=pk)
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

    Domains.fix_all()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domains_read_bookmarks(request):
    p = ViewPage(request)
    p.set_title("Read domains from bookmarks")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    LinkDataHyperController.read_domains_from_bookmarks()

    return HttpResponseRedirect(reverse("{}:domains".format(LinkDatabase.name)))


def domain_json(request, pk):
    domains = Domains.objects.filter(id=pk)

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

    domains = Domains.objects.all()

    # Data
    query_filter = DomainFilter(request.GET)
    query_filter.use_page_limit = True
    domains = query_filter.get_filtered_objects()

    from ..serializers.domainexporter import DomainJsonExporter

    exp = DomainJsonExporter()

    # JsonResponse
    return JsonResponse(exp.get_json(domains))
