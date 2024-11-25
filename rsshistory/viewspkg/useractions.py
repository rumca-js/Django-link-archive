from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import JsonResponse

from datetime import datetime, timedelta
from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..models import (
    UserTags,
    CompactedTags,
    UserCompactedTags,
    ConfigurationEntry,
    UserVotes,
)
from ..configuration import Configuration
from ..controllers import LinkDataController, EntryWrapper
from ..forms import TagForm, TagEditForm, TagRenameForm, ScannerForm, LinkVoteForm
from ..views import ViewPage, GenericListView, UserGenericListView


class CompactedTagsListView(GenericListView):
    model = CompactedTags
    context_object_name = "content_list"
    paginate_by = 9200
    template_name = str(ViewPage.get_full_template("tags_list.html"))

    def get_tags_objects(self):
        return CompactedTags.objects.all()

    def get_queryset(self):
        """
        TODO: maybe add aggregation SQL, count on tags?
        """
        objects = self.get_tags_objects()

        return objects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = ViewPage(self.request).init_context(context)

        context["page_title"] += " " + self.get_title()
        context["tags_title"] = "Tags"

        return context

    def get_title(self):
        return "Tags"


class UserCompactedTagsListView(UserGenericListView):
    model = UserCompactedTags
    context_object_name = "content_list"
    paginate_by = 9200
    template_name = str(ViewPage.get_full_template("tags_list.html"))

    def get_title(self):
        return "Tags"


class ActualTags(UserGenericListView):
    model = UserTags
    context_object_name = "content_list"
    paginate_by = 9200
    template_name = str(ViewPage.get_full_template("tags_list.html"))

    def get_time_range(self):
        return DateUtils.get_days_range()

    def get_queryset(self):
        """
        TODO: maybe add aggregation SQL, count on tags?
        """
        objects = self.get_tags_objects()

        tags = objects.values("tag")

        result = {}
        for item in tags:
            tag = item["tag"]
            if tag in result:
                result[item["tag"]] += 1
            else:
                result[item["tag"]] = 1

        self.result_list = []
        for item in result:
            self.result_list.append([item, result[item]])

        self.result_list = sorted(
            self.result_list, key=lambda x: (x[1], x[0]), reverse=True
        )

        return objects

    def get_tags_objects(self):
        return UserTags.objects.filter(date__range=self.get_time_range())

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)
        time_range = self.get_time_range()
        context["tags_title"] = "Recent tags: {} {}".format(
            time_range[0], time_range[1]
        )

        return context

    def get_title(self):
        return "Tags"


def entry_tags(request, pk):
    p = ViewPage(request)
    p.set_title("Tag entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    operation_data = {}

    entries = LinkDataController.objects.filter(id=pk)

    if not entries.exists():
        operation_data["message"] = "Entry does not exist"
        operation_data["status"] = False
        return JsonResponse(operation_data, json_dumps_params={"indent":4})

    entry = entries[0]
    if not entry.is_taggable():
        operation_data["message"] = "Cannot tag entry"
        operation_data["status"] = False
        return JsonResponse(operation_data, json_dumps_params={"indent":4})

    operation_data["tags"] = entry.get_tag_map()  # vector
    operation_data["status"] = True

    return JsonResponse(operation_data, json_dumps_params={"indent":4})


def entry_tag(request, pk):
    p = ViewPage(request)
    p.set_title("Tag entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/

    operation_data = {}

    entries = LinkDataController.objects.filter(id=pk)

    if not entries.exists():
        operation_data["message"] = "Entry does not exist"
        operation_data["status"] = False
        return JsonResponse(operation_data, json_dumps_params={"indent":4})

    entry = entries[0]
    if not entry.is_taggable():
        operation_data["message"] = "Cannot tag entry"
        operation_data["status"] = False
        return JsonResponse(operation_data, json_dumps_params={"indent":4})

    if request.method == "POST":
        method = "POST"

        form = TagEditForm(request.POST)

        if form.is_valid():
            tag_string = form.cleaned_data["tags"]
            UserTags.set_tags(entry, tag_string, user=request.user)

            operation_data["message"] = "Tagged entry"
            operation_data["tags"] = entry.get_tag_map()  # vector
            operation_data["status"] = True
            return JsonResponse(operation_data, json_dumps_params={"indent":4})

        else:
            summary_text = "Cannot add tag due to errors: "
            errors = form.errors
            for field, error_msgs in errors.items():
                for error_msg in error_msgs:
                    summary_text += " Field:{} Problem:{}".format(field, error_msg)

            operation_data["message"] = summary_text
            operation_data["status"] = False
            return JsonResponse(operation_data, json_dumps_params={"indent":4})

    return JsonResponse(operation_data, json_dumps_params={"indent":4})


def entry_tag_form(request, pk):
    p = ViewPage(request)
    p.set_title("Tag entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/

    p.context["page_title"] += " - tag entry"

    entries = LinkDataController.objects.filter(id=pk)

    if not entries.exists():
        # TODO return html that can be inserted
        return

    entry = entries[0]
    if not entry.is_taggable():
        # TODO return html that can be inserted
        return

    user = request.user
    tag_string = UserTags.get_user_tag_string(request.user, entry)

    data_init = {"entry_id": entry.id}

    if tag_string:
        data_init["tags"] = tag_string

    form = TagEditForm(initial=data_init)

    form.method = "POST"
    form.pk = pk
    form.action_url = reverse("{}:entry-tag".format(LinkDatabase.name), args=[pk])
    p.context["form"] = form
    p.context["form_title"] = entry.title
    p.context["form_description"] = entry.title
    p.context["form_description_pre"] = entry.link
    p.context["pk"] = pk

    return p.render("entry_detail__tag_form.html")


def tag_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove a tag")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = UserTags.objects.get(id=pk)
    entry.delete()

    return HttpResponseRedirect(reverse("{}:tags-show-all".format(LinkDatabase.name)))


def tags_remove_all(request):
    p = ViewPage(request)
    p.set_title("Tags removed")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = UserTags.objects.all().delete()

    # TODO recalculate entries?

    return HttpResponseRedirect(reverse("{}:index".format(LinkDatabase.name)))


def tag_remove_form(request):
    p = ViewPage(request)
    p.set_title("Remove tag form")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = TagForm(request.POST)

        if form.is_valid():
            tag_name = form.cleaned_data["tag"]

            tags = UserTags.objects.filter(tag=tag_name)
            tags.delete()

            return HttpResponseRedirect(
                reverse("{}:tags-show-all".format(LinkDatabase.name))
            )

        p.context["summary_text"] = "Invalid form"
        return p.render("summary_present.html")
    else:
        form = TagForm()

        form.method = "POST"
        form.action_url = reverse("{}:tag-remove-form".format(LinkDatabase.name))

        p.context["form"] = form
        p.context["form_title"] = "Remove tag"
        p.context["form_description"] = "Remove tag"

        return p.render("form_basic.html")

    return p.render("summary_present.html")


def tag_remove_str(request, tag_name):
    p = ViewPage(request)
    p.set_title("Remove tag")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entries = UserTags.objects.filter(tag=tag_name)
    entries.delete()

    return HttpResponseRedirect(reverse("{}:tags-show-all".format(LinkDatabase.name)))


def tags_entry_remove(request, entrypk):
    p = ViewPage(request)
    p.set_title("Remove tag")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkDataController.objects.get(id=entrypk)
    tags = entry.tags.all()
    for tag in tags:
        tag.delete()

    return HttpResponseRedirect(reverse("{}:tags-show-all".format(LinkDatabase.name)))


def tags_entry_show(request, entrypk):
    p = ViewPage(request)
    p.set_title("Show tag entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    summary = ""

    entry = LinkDataController.objects.get(id=entrypk)
    tags = entry.tags.all()
    for tag in tags:
        summary += "Link:{} tag:{} user:{}\n".format(
            tag.entry.link, tag.tag, tag.user.username
        )

    p.context["summary_text"] = summary

    return p.render("summary_present.html")


def tag_rename(request):
    p = ViewPage(request)
    p.set_title("Rename a tag")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    if request.method == "POST":
        form = TagRenameForm(request.POST)

        if form.is_valid():
            current_tag = form.cleaned_data["current_tag"]
            new_tag = form.cleaned_data["new_tag"]

            tags = UserTags.objects.filter(tag=current_tag)
            for tag in tags:
                tag.tag = new_tag.lower()
                tag.save()

            return HttpResponseRedirect(
                reverse("{}:tags-show-all".format(LinkDatabase.name))
            )

        p.context["summary_text"] = "Invalid form"
        return p.render("summary_present.html")
    else:
        form = TagRenameForm()

        form.method = "POST"
        form.action_url = reverse("{}:tag-rename".format(LinkDatabase.name))

        p.context["form"] = form
        p.context["form_title"] = "Rename tag"
        p.context["form_description"] = "Rename tag"

        return p.render("form_basic.html")

    return p.render("summary_present.html")


def tag_many(request):
    p = ViewPage(request)
    p.set_title("Tag many links")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    from ..forms import ExportDailyDataForm

    if request.method == "POST":
        errors = []

        form = ScannerForm(request.POST)
        if not form.is_valid():
            return p.render("form_basic.html")

        links = form.cleaned_data["body"]
        tag = form.cleaned_data["tag"]

        links = links.split("\n")
        for link in links:
            link = link.strip()
            link = link.replace("\r", "")

            if link != "":
                w = EntryWrapper(link=link)
                entry = w.get()
                if entry and not entry.is_archive_entry():
                    entry.set_tag(tag_name=tag, user=request.user)
                else:
                    errors.append("{} not exist, or is archive".format(entry))

        p.context["summary_text"] = "Tagged links\nErrors:{}".format(errors)
        return p.render("summary_present.html")
    else:
        form = ScannerForm()
        form.method = "POST"

        p.context["form"] = form

        return p.render("form_basic.html")


def votes_remove_all(request):
    p = ViewPage(request)
    p.set_title("Tags removed")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = UserVotes.objects.all().delete()

    # TODO recalculate entries?

    return HttpResponseRedirect(reverse("{}:index".format(LinkDatabase.name)))


def entry_vote(request, pk):
    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/

    p = ViewPage(request)
    p.set_title("Vote for entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    p.context["pk"] = pk

    operation_data = {}
    entries = LinkDataController.objects.filter(id=pk)

    if not entries.exists():
        operation_data["message"] = "Entry does not exist"
        operation_data["status"] = False
        return JsonResponse(operation_data, json_dumps_params={"indent":4})

    entry = entries[0]
    if not entry.is_taggable():
        operation_data["message"] = "Cannot vote on entry"
        operation_data["status"] = False
        return JsonResponse(operation_data, json_dumps_params={"indent":4})

    if request.method == "POST":
        method = "POST"

        form = LinkVoteForm(request.POST)

        if form.is_valid():
            data = {}
            data["user"] = request.user
            data["entry"] = entry
            data["vote"] = form.cleaned_data["vote"]
            UserVotes.save_vote(data)

            operation_data["message"] = "Voted"
            operation_data["vote"] = data["vote"]
            operation_data["status"] = True
            return JsonResponse(operation_data, json_dumps_params={"indent":4})
        else:
            summary_text = "Cannot add tag due to errors: "
            errors = form.errors
            for field, error_msgs in errors.items():
                for error_msg in error_msgs:
                    summary_text += " Field:{} Problem:{}".format(field, error_msg)

            operation_data["message"] = summary_text
            operation_data["status"] = False
            return JsonResponse(operation_data, json_dumps_params={"indent":4})


def entry_vote_form(request, pk):
    user = request.user

    p = ViewPage(request)
    p.set_title("Vote for entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    p.context["pk"] = pk

    entries = LinkDataController.objects.filter(id=pk)

    if not entries.exists():
        return

    entry = entries[0]
    if not entry.is_taggable():
        return

    vote = UserVotes.get_user_vote(user, entry)

    form = LinkVoteForm(
        initial={
            "entry_id": entry.id,
            "vote": vote,
        }
    )

    form.method = "POST"
    form.pk = pk
    form.action_url = reverse("{}:entry-vote".format(LinkDatabase.name), args=[pk])

    p.context["form"] = form
    p.context["form_title"] = entry.title
    p.context["form_description"] = entry.title

    return p.render("entry_detail__vote_form.html")
