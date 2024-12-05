from django.views import generic
from django.urls import reverse
from django.shortcuts import redirect
from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.http import urlencode
from django.core.paginator import Paginator

from utils.omnisearch import SingleSymbolEvaluator

from ..apps import LinkDatabase
from ..models import (
    Domains,
    ConfigurationEntry,
    UserConfig,
)
from ..controllers import (
    EntryWrapper,
    EntryDataBuilder,
    LinkDataController,
    DomainsController,
    SearchEngines,
)
from ..views import ViewPage, GenericListView
from ..forms import DomainsChoiceForm, DomainEditForm, LinkInputForm
from ..queryfilters import DomainFilter
from ..views import (
    ViewPage,
    get_search_term,
    get_order_by,
    get_page_num,
)


class DomainsListView(object):
    paginate_by = 100

    def __init__(self, request):
        self.request = request
        self.user = user
        if not self.user and self.request:
            self.user = self.request.user

    def get_queryset(self):
        self.query_filter = DomainFilter(self.request.GET, user=self.user)
        return self.query_filter.get_filtered_objects()

    def get_title(self):
        return "Domains"

    def get_paginate_by(self):
        if not self.user or not self.user.is_authenticated:
            config = Configuration.get_object().config_entry
            return config.links_per_page
        else:
            uc = UserConfig.get(self.user)
            return uc.links_per_page


class DomainsDetailView(generic.DetailView):
    model = DomainsController
    context_object_name = "domain_detail"
    template_name = str(ViewPage.get_full_template("domains_detail.html"))

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
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        if self.object and self.object.domain:
            context["page_title"] += " {} domain".format(self.object.domain)

        return context


def get_generic_search_init_context(request, form, user_choices):
    context = {}
    context["form"] = form

    search_term = get_search_term(request.GET)
    context["search_term"] = search_term
    context["search_engines"] = SearchEngines(search_term)
    context["search_history"] = user_choices
    context["view_link"] = form.action_url
    context["form_submit_button_name"] = "Search"

    context["entry_query_names"] = DomainsController.get_query_names()
    context["entry_query_operators"] = SingleSymbolEvaluator().get_operators()

    return context


def domains(request):
    p = ViewPage(request)
    p.set_title("Domains")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    data = {}
    if "search" in request.GET:
        data = {"search": request.GET["search"]}

    filter_form = DomainsChoiceForm(request=request, initial=data)
    filter_form.method = "GET"
    filter_form.action_url = reverse("{}:domains".format(LinkDatabase.name))

    # TODO jquery that
    # user_choices = UserSearchHistory.get_user_choices(request.user)
    user_choices = []
    context = get_generic_search_init_context(request, filter_form, user_choices)

    p.context.update(context)
    p.context["query_page"] = reverse("{}:domains-json".format(LinkDatabase.name))

    p.context["search_suggestions_page"] = None
    p.context["search_history_page"] = None

    return p.render("domains_list.html")


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

    return JsonResponse(domain, json_dumps_params={'indent':4})


def domain_to_json(user_config, domain):
    json = {}
    json["id"] = domain.id
    json["domain"] = domain.domain
    json["main"] = domain.main
    json["subdomain"] = domain.subdomain
    json["suffix"] = domain.suffix
    json["tld"] = domain.tld

    return json


def domains_json(request):
    p = ViewPage(request)
    p.set_title("Returns all domains JSON")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    page_num = p.get_page_num()

    json_obj = {}
    json_obj["domains"] = []
    json_obj["count"] = 0
    json_obj["page"] = page_num
    json_obj["num_pages"] = 0

    view = DomainsListView(request)

    uc = UserConfig.get(request.user)

    domains = view.get_queryset()
    p = Paginator(domains, view.get_paginate_by())
    page_obj = p.get_page(page_num)

    json_obj["count"] = p.count
    json_obj["num_pages"] = p.num_pages

    start = page_obj.start_index()
    if start > 0:
        start -= 1

    limited_domains = domains[start : page_obj.end_index()]

    if page_num <= p.num_pages:
        for domain in limited_domains:
            domain_json = domain_to_json(uc, domain)

            json_obj["domains"].append(domain_json)

    return JsonResponse(json_obj, json_dumps_params={"indent":4})


def domains_reset_dynamic_data(request):
    p = ViewPage(request)
    p.set_title("Reset dynamic data")

    DomainsController.reset_dynamic_data()

    return redirect("{}:domains".format(LinkDatabase.name))
