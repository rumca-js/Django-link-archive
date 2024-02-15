from django.views import generic
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden, HttpResponseRedirect

from datetime import datetime, timedelta

from ..apps import LinkDatabase
from ..models import LinkTagsDataModel, ConfigurationEntry, LinkVoteDataModel
from ..controllers import LinkDataController
from ..forms import TagForm, TagEntryForm, TagRenameForm
from ..views import ViewPage


class AllTags(generic.ListView):
    model = LinkTagsDataModel
    context_object_name = "content_list"
    paginate_by = 9200
    template_name = str(ViewPage.get_full_template("tags_list.html"))

    def get(self, *args, **kwargs):
        p = ViewPage(self.request)
        data = p.check_access()
        if data:
            return redirect("{}:missing-rights".format(LinkDatabase.name))
        return super(AllTags, self).get(*args, **kwargs)

    def get_tags_objects(self):
        return LinkTagsDataModel.objects.all()

    def get_queryset(self):
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

    def get_context_data(self, **kwargs):
        context = super(AllTags, self).get_context_data(**kwargs)
        context = ViewPage.init_context(self.request, context)

        context["page_title"] += " - all tags"
        context["tag_objects"] = self.result_list
        context["tags_title"] = "All tags"

        return context


class RecentTags(AllTags):
    model = LinkTagsDataModel
    context_object_name = "tags_list"
    paginate_by = 9200
    template_name = str(ViewPage.get_full_template("tags_list.html"))

    def get_time_range(self):
        from ..dateutils import DateUtils

        return DateUtils.get_days_range()

    def get_tags_objects(self):
        return LinkTagsDataModel.objects.filter(date__range=self.get_time_range())

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RecentTags, self).get_context_data(**kwargs)
        time_range = self.get_time_range()
        context["tags_title"] = "Recent tags: {} {}".format(
            time_range[0], time_range[1]
        )

        return context


def tag_entry(request, pk):
    p = ViewPage(request)
    p.set_title("Tag entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/

    p.context["page_title"] += " - tag entry"
    p.context["pk"] = pk

    objs = LinkDataController.objects.filter(id=pk)

    if not objs.exists():
        p.context["summary_text"] = "Sorry, such object does not exist"
        return p.render("summary_present.html")

    obj = objs[0]
    if not obj.is_taggable():
        p.context["summary_text"] = "Sorry, only bookmarked objects can be tagged"
        return p.render("summary_present.html")

    if request.method == "POST":
        method = "POST"

        form = TagEntryForm(request.POST)

        if form.is_valid():
            LinkTagsDataModel.set_tags(form.cleaned_data)

            return HttpResponseRedirect(
                reverse(
                    "{}:entry-detail".format(LinkDatabase.name),
                    kwargs={"pk": obj.pk},
                )
            )
        else:
            p.context["summary_text"] = "Entry not added"
            return p.render("summary_present.html")

    else:
        user = request.user
        link = obj.link
        tag_string = LinkTagsDataModel.get_user_tag_string(request.user, link)

        if tag_string:
            form = TagEntryForm(
                initial={"link": link, "user": user, "tag": tag_string}
            )
        else:
            form = TagEntryForm(initial={"link": link, "user": user})

        form.method = "POST"
        form.pk = pk
        form.action_url = reverse("{}:entry-tag".format(LinkDatabase.name), args=[pk])
        p.context["form"] = form
        p.context["form_title"] = obj.title
        p.context["form_description"] = obj.title

    return p.render("form_basic.html")


def tag_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove a tag")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    entry = LinkTagsDataModel.objects.get(id=pk)
    entry.delete()

    return HttpResponseRedirect(reverse("{}:tags-show-all".format(LinkDatabase.name)))


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

            tags = LinkTagsDataModel.objects.filter(tag=tag_name)
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

    entries = LinkTagsDataModel.objects.filter(tag=tag_name)
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
        summary += "Link:{} tag:{} user:{}\n".format(tag.link, tag.tag, tag.user)

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

            tags = LinkTagsDataModel.objects.filter(tag=current_tag)
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


def entry_vote(request, pk):
    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/
    from ..forms import LinkVoteForm

    p = ViewPage(request)
    p.set_title("Vote for entry")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_STAFF)
    if data is not None:
        return data

    p.context["pk"] = pk

    objs = LinkDataController.objects.filter(id=pk)

    if not objs.exists():
        p.context["summary_text"] = "Sorry, such object does not exist"
        return p.render("summary_present.html")

    obj = objs[0]
    if not obj.is_taggable():
        p.context["summary_text"] = "Sorry, only bookmarked objects can be tagged"
        return p.render("summary_present.html")

    if request.method == "POST":
        method = "POST"

        form = LinkVoteForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            data["user"] = request.user
            LinkVoteDataModel.save_vote(data)

            return HttpResponseRedirect(
                reverse(
                    "{}:entry-detail".format(LinkDatabase.name),
                    kwargs={"pk": obj.pk},
                )
            )
        else:
            config = Configuration.get_object().config_entry
            p.context[
                "summary_text"
            ] = "Entry not voted. Vote min, max = [{}, {}]".format(
                config.vote_min, config.vote_max
            )
            return p.render("summary_present.html")

    else:
        user = request.user

        vote = 0
        votes = obj.votes.filter(user=user)
        if votes.count() > 0:
            vote = votes[0].vote

        form = LinkVoteForm(initial={"link_id": obj.id, "user": user, "vote": vote})

        form.method = "POST"
        form.pk = pk
        form.action_url = reverse("{}:entry-vote".format(LinkDatabase.name), args=[pk])

        p.context["form"] = form
        p.context["form_title"] = obj.title
        p.context["form_description"] = obj.title

    return p.render("form_basic.html")
