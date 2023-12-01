from pathlib import Path
import traceback, sys

from django.views import generic
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseRedirect

from ..models import (
    LinkCommentDataModel,
    ConfigurationEntry,
)
from ..forms import CommentEntryForm
from ..views import ViewPage
from ..controllers import LinkCommentDataController, LinkDataController
from ..apps import LinkDatabase


def entry_add_comment(request, link_id):
    p = ViewPage(request)
    p.set_title("Add comment")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    user_name = request.user.get_username()
    if not LinkCommentDataController.can_user_add_comment(link_id, user_name):
        p.context[
            "summary_text"
        ] = "User cannot add more comments. Limit to {} comment per day".format(
            config.number_of_comments_per_day
        )
        return p.render("summary_present.html")

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
                    "{}:entry-detail".format(LinkDatabase.name),
                    kwargs={"pk": link.pk},
                )
            )

        p.context["summary_text"] = "Could not add a comment"
        return p.render("summary_present.html")

    else:
        author = request.user.username
        form = CommentEntryForm(initial={"author": author, "link_id": link.id})

    form.method = "POST"
    form.pk = link_id
    form.action_url = reverse(
        "{}:entry-comment-add".format(LinkDatabase.name), args=[link_id]
    )

    p.context["form"] = form
    p.context["form_title"] = link.title
    p.context[
        "form_description_post"
    ] = """Please think twice about what you are going to say. Is it written in vengance? Is it something you truly believe? Have you done research in that matter? This is important. You will be able to post only 1 comment per day"""

    return p.render("form_basic.html")


def entry_comment_edit(request, pk):
    p = ViewPage(request)
    p.set_title("Edit comment")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    comment_obj = LinkCommentDataModel.objects.get(id=pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        p.context["summary_text"] = "You are not the author!"
        return p.render("summary_present.html")

    if request.method == "POST":
        form = CommentEntryForm(request.POST)

        if form.is_valid():
            comment_obj.comment = form.cleaned_data["comment"]
            comment_obj.save()

            p.context["summary_text"] = "Comment edited"

            return p.render("summary_present.html")
        else:
            p.context["summary_text"] = "Form is not valid"

            return p.render("summary_present.html")
    else:
        data = {
            "link_id": link.id,
            "author": author,
            "comment": comment_obj.comment,
            "date_published": comment_obj.date_published,
        }
        form = CommentEntryForm(initial=data)

        form.method = "POST"
        form.pk = pk
        form.action_url = reverse(
            "{}:entry-comment-edit".format(LinkDatabase.name), args=[pk]
        )

        p.context["form"] = form
        p.context["form_title"] = link.title
        p.context["form_description"] = link.title

        return p.render("form_basic.html")


def entry_comment_remove(request, pk):
    p = ViewPage(request)
    p.set_title("Remove comment")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_LOGGED)
    if data is not None:
        return data

    comment_obj = LinkCommentDataModel.objects.get(id=pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        p.context["summary_text"] = "You are not the author!"
        return p.render("summary_present.html")

    comment_obj.delete()

    p.context["summary_text"] = "Removed comment"

    return p.render("summary_present.html")
