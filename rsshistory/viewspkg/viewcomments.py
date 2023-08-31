from pathlib import Path
import traceback, sys

from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..models import (
    ConfigurationEntry,
    LinkTagsDataModel,
    LinkCommentDataModel,
)
from ..configuration import Configuration
from ..forms import CommentEntryForm
from ..views import ContextData
from ..controllers import LinkCommentDataController, LinkDataController


def entry_add_comment(request, link_id):
    context = ContextData.get_context(request)
    context["page_title"] += " - Add comment"

    if not request.user.is_authenticated:
        return ContextData.render(request, "missing_rights.html", context)

    user_name = request.user.get_username()
    if not LinkCommentDataController.can_user_add_comment(link_id, user_name):
        conf = ConfigurationEntry.get()
        context["summary_text"] = "User cannot add more comments. Limit to {} comment per day".format(config.number_of_comments_per_day)
        return ContextData.render(request, "summary_present.html", context)

    print("Link id" + str(link_id))
    link = LinkDataController.objects.get(id=link_id)

    # if this is a POST request we need to process the form data
    if request.method == "POST":
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = CommentEntryForm(request.POST)
        if form.is_valid():
            LinkCommentDataController.save_comment(form.cleaned_data)

            return HttpResponseRedirect(
                reverse(
                    "{}:entry-detail".format(ContextData.app_name),
                    kwargs={"pk": link.pk},
                )
            )

        context["summary_text"] = "Could not add a comment"

        return ContextData.render(request, "summary_present.html", context)

    else:
        author = request.user.username
        form = CommentEntryForm(initial={"author": author, "link_id": link.id})

    form.method = "POST"
    form.pk = link_id
    form.action_url = reverse(
        "{}:entry-comment-add".format(ContextData.app_name), args=[link_id]
    )

    context["form"] = form
    context["form_title"] = link.title
    context[
        "form_description_post"
    ] = """Please think twice about what you are going to say. Is it written in vengance? Is it something you truly believe? Have you done research in that matter? This is important. You will be able to post only 1 comment per day"""

    return ContextData.render(request, "form_basic.html", context)


def entry_comment_edit(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - edit comment"

    if not request.user.is_authenticated:
        return ContextData.render(request, "missing_rights.html", context)

    comment_obj = LinkCommentDataModel.objects.get(id=pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        context["summary_text"] = "You are not the author!"
        return ContextData.render(request, "summary_present.html", context)

    if request.method == "POST":
        form = CommentEntryForm(request.POST)

        if form.is_valid():
            comment_obj.comment = form.cleaned_data["comment"]
            comment_obj.save()

            context["summary_text"] = "Comment edited"

            return ContextData.render(request, "summary_present.html", context)
        else:
            context["summary_text"] = "Form is not valid"

            return ContextData.render(request, "summary_present.html", context)
    else:
        form = CommentEntryForm(instance=comment_obj)
        form.method = "POST"
        form.pk = pk
        form.action_url = reverse(
            "{}:entry-comment-edit".format(ContextData.app_name), args=[pk]
        )

        context["form"] = form
        context["form_title"] = link.title
        context["form_description"] = link.title

        return ContextData.render(request, "form_basic.html", context)


def entry_comment_remove(request, pk):
    context = ContextData.get_context(request)
    context["page_title"] += " - remove comment"

    if not request.user.is_authenticated:
        return ContextData.render(request, "missing_rights.html", context)

    comment_obj = LinkCommentDataModel.objects.get(id=pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        context["summary_text"] = "You are not the author!"
        return ContextData.render(request, "summary_present.html", context)

    comment_obj.delete()

    context["summary_text"] = "Removed comment"

    return ContextData.render(request, "summary_present.html", context)
