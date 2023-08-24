from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseRedirect

from datetime import datetime, timedelta

from ..models import LinkTagsDataModel
from ..configuration import Configuration
from ..forms import ConfigForm
from ..views import ContextData
from ..controllers import LinkDataController


class AllTags(generic.ListView):
    model = LinkTagsDataModel
    context_object_name = "content_list"
    paginate_by = 9200

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
        context = ContextData.init_context(self.request, context)

        context["page_title"] += " - all tags"
        context["tag_objects"] = self.result_list
        context["tags_title"] = "All tags"

        return context


class RecentTags(AllTags):
    model = LinkTagsDataModel
    context_object_name = "tags_list"
    paginate_by = 9200

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
    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/
    from ..forms import TagEntryForm

    context = ContextData.get_context(request)
    context["page_title"] += " - tag entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    objs = LinkDataController.objects.filter(id=pk)

    if not objs.exists():
        context["summary_text"] = "Sorry, such object does not exist"
        return ContextData.render(request, "summary_present.html", context)

    obj = objs[0]
    if not obj.persistent:
        context["summary_text"] = "Sorry, only persistent objects can be tagged"
        return ContextData.render(request, "summary_present.html", context)

    if request.method == "POST":
        method = "POST"

        form = TagEntryForm(request.POST)

        if form.is_valid():
            form.save_tags()

            return HttpResponseRedirect(
                    reverse("{}:entry-detail".format(ContextData.app_name), kwargs={"pk": obj.pk})
            )
        else:
            context["summary_text"] = "Entry not added"
            return ContextData.render(request, "summary_present.html", context)

    else:
        author = request.user.username
        link = obj.link
        tag_string = LinkTagsDataModel.get_author_tag_string(author, link)

        if tag_string:
            form = TagEntryForm(
                initial={"link": link, "author": author, "tag": tag_string}
            )
        else:
            form = TagEntryForm(initial={"link": link, "author": author})

        form.method = "POST"
        form.pk = pk
        form.action_url = reverse(
            "{}:entry-tag".format(ContextData.app_name), args=[pk]
        )
        context["form"] = form
        context["form_title"] = obj.title
        context["form_description"] = obj.title

    return ContextData.render(request, "form_basic.html", context)


def tag_remove(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove tag"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    entry = LinkTagsDataModel.objects.get(id=pk)
    entry.delete()

    context["summary_text"] = "Remove ok"

    return ContextData.render(request, "summary_present.html", context)


def tags_entry_remove(request, entrypk):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove tag"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    entry = LinkDataController.objects.get(id=entrypk)
    tags = entry.tags.all()
    for tag in tags:
        tag.delete()

    context["summary_text"] = "Remove ok"

    return ContextData.render(request, "summary_present.html", context)


def tags_entry_show(request, entrypk):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove tag"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    summary = ""

    entry = LinkDataController.objects.get(id=entrypk)
    tags = entry.tags.all()
    for tag in tags:
        summary += "Link:{} tag:{} author:{}\n".format(tag.link, tag.tag, tag.author)

    context["summary_text"] = summary

    return ContextData.render(request, "summary_present.html", context)


def tag_rename(request):
    from ..forms import TagRenameForm

    context = ContextData.get_context(request)
    context["page_title"] += " - rename tag"

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    if request.method == "POST":
        form = TagRenameForm(request.POST)

        if form.is_valid():
            current_tag = form.cleaned_data["current_tag"]
            new_tag = form.cleaned_data["new_tag"]

            tags = LinkTagsDataModel.objects.filter(tag=current_tag)
            for tag in tags:
                tag.tag = new_tag.lower()
                tag.save()

            summary_text = "Renamed tags"
            context["summary_text"] = summary_text

        return ContextData.render(request, "summary_present.html", context)
    else:
        form = TagRenameForm()

        form.method = "POST"
        form.action_url = reverse("{}:tag-rename".format(ContextData.app_name))

        context["form"] = form
        context["form_title"] = "Rename tag"
        context["form_description"] = "Rename tag"

        return ContextData.render(request, "form_basic.html", context)

    return ContextData.render(request, "summary_present.html", context)


def entry_vote(request, pk):
    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/
    from ..forms import LinkVoteForm

    context = ContextData.get_context(request)
    context["page_title"] += " - vote entry"
    context["pk"] = pk

    if not request.user.is_staff:
        return ContextData.render(request, "missing_rights.html", context)

    objs = LinkDataController.objects.filter(id=pk)

    if not objs.exists():
        context["summary_text"] = "Sorry, such object does not exist"
        return ContextData.render(request, "summary_present.html", context)

    obj = objs[0]
    if not obj.persistent:
        context["summary_text"] = "Sorry, only persistent objects can be tagged"
        return ContextData.render(request, "summary_present.html", context)

    if request.method == "POST":
        method = "POST"

        form = LinkVoteForm(request.POST)

        if form.is_valid():
            form.save_vote()

            return HttpResponseRedirect(
                    reverse("{}:entry-detail".format(ContextData.app_name), kwargs={"pk": obj.pk})
            )
        else:
            context["summary_text"] = "Entry not voted"
            return ContextData.render(request, "summary_present.html", context)

    else:
        author = request.user.username

        vote = 0
        votes = obj.votes.filter(author=author)
        if len(votes) > 0:
            vote = votes[0].vote

        form = LinkVoteForm(initial={"link_id": obj.id, "author": author, "vote": vote})

        form.method = "POST"
        form.pk = pk
        form.action_url = reverse(
            "{}:entry-vote".format(ContextData.app_name), args=[pk]
        )
        context["form"] = form
        context["form_title"] = obj.title
        context["form_description"] = obj.title

    return ContextData.render(request, "form_basic.html", context)
