from pathlib import Path
import traceback, sys

from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..models import SourceDataModel, LinkDataModel, LinkTagsDataModel, LinkCommentDataModel
from ..prjconfig import Configuration
from ..forms import CommentEntryForm


def init_context(request, context):
    from ..views import init_context
    return init_context(request, context)


def get_context(request):
    from ..views import get_context
    return get_context(request)


def get_app():
    from ..views import app_name
    return app_name


def entry_add_comment(request, link_id):
    context = get_context(request)
    context['page_title'] += " - Add comment"

    if not request.user.is_authenticated:
        return render(request, get_app() / 'missing_rights.html', context)

    print("Link id" + str(link_id))
    link = LinkDataModel.objects.get(id=link_id)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = CommentEntryForm(request.POST)
        if form.is_valid():
            form.save_comment()

            context["summary_text"] = "Added a new comment"
            return render(request, get_app() / 'summary_present.html', context)

        context["summary_text"] = "Could not add a comment"

        return render(request, get_app() / 'summary_present.html', context)

    else:
        author = request.user.username
        form = CommentEntryForm(initial={'author': author, 'link': link.link})

    form.method = "POST"
    form.pk = link_id
    form.action_url = reverse('{}:entry-comment-add'.format(get_app()), args=[link_id])

    context['form'] = form
    context['form_title'] = link.title
    context['form_description'] = link.title

    return render(request, get_app() / 'form_basic.html', context)


def entry_comment_edit(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit comment"

    if not request.user.is_authenticated:
        return render(request, get_app() / 'missing_rights.html', context)

    comment_obj = LinkCommentDataModel.objects.get(id=pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        context["summary_text"] = "You are not the author!"
        return render(request, get_app() / 'summary_present.html', context)

    if request.method == 'POST':
        form = CommentEntryForm(request.POST)

        if form.is_valid():
            comment_obj.comment = form.cleaned_data['comment']
            comment_obj.save()

            context["summary_text"] = "Comment edited"

            return render(request, get_app() / 'summary_present.html', context)
        else:
            context["summary_text"] = "Form is not valid"

            return render(request, get_app() / 'summary_present.html', context)
    else:
        form = CommentEntryForm(instance=comment_obj)
        form.method = "POST"
        form.pk = pk
        form.action_url = reverse('{}:entry-comment-edit'.format(get_app()), args=[pk])

        context['form'] = form
        context['form_title'] = link.title
        context['form_description'] = link.title

        return render(request, get_app() / 'form_basic.html', context)


def entry_comment_remove(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove comment"

    if not request.user.is_authenticated:
        return render(request, get_app() / 'missing_rights.html', context)

    comment_obj = LinkCommentDataModel.objects.get(id=pk)
    link = comment_obj.link_obj

    author = request.user.username

    if author != comment_obj.author:
        context["summary_text"] = "You are not the author!"
        return render(request, get_app() / 'summary_present.html', context)

    comment_obj.delete()

    context["summary_text"] = "Removed comment"

    return render(request, get_app() / 'summary_present.html', context)
