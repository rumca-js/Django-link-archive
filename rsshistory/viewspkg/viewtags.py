from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..models import RssSourceDataModel, RssSourceEntryDataModel, ConfigurationEntry
from ..models import RssEntryTagsDataModel
from ..prjconfig import Configuration
from ..forms import SourceForm, EntryForm, ImportSourcesForm, ImportEntriesForm, SourcesChoiceForm, ConfigForm, CommentEntryForm


def init_context(context):
    from ..views import init_context
    return init_context(context)

def get_context(request):
    from ..views import get_context
    return get_context(request)

def get_app():
    from ..views import app_name
    return app_name


def show_tags(request):

    context = get_context(request)
    context['page_title'] += " - browse tags"

    # TODO select only this month
    objects = RssEntryTagsDataModel.objects.all()

    tags = objects.values('tag')

    result = {}
    for item in tags:
        tag = item['tag']
        if tag in result:
            result[item['tag']] += 1
        else:
            result[item['tag']] = 1

    result_list = []
    for item in result:
        result_list.append([item, result[item]])

    def map_func(elem):
        return elem[1]

    result_list = sorted(result_list, key = map_func, reverse=True)

    text = ""
    for tag in result_list:
        link = reverse('rsshistory:entries') + "?tag="+tag[0]
        link_text = str(tag[0]) + " " + str(tag[1])
        text += "<div><a href=\"{0}\" class=\"simplebutton\">{1}</a></div>".format(link, link_text)

    context["summary_text"] = text

    return render(request, get_app() / 'tags_view.html', context)


def tag_entry(request, pk):
    # TODO read and maybe fix https://docs.djangoproject.com/en/4.1/topics/forms/modelforms/
    from ..forms import TagEntryForm

    context = get_context(request)
    context['page_title'] += " - tag entry"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    objs = RssSourceEntryDataModel.objects.filter(id=pk)

    if not objs.exists():
        context["summary_text"] = "Sorry, such object does not exist"
        return render(request, get_app() / 'summary_present.html', context)

    obj = objs[0]
    if not obj.persistent:
        context["summary_text"] = "Sorry, only persistent objects can be tagged"
        return render(request, get_app() / 'summary_present.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = TagEntryForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            form.save_tags()

            context["summary_text"] = "Entry tagged"
            return render(request, get_app() / 'summary_present.html', context)
        else:
            context["summary_text"] = "Entry not added"
            return render(request, get_app() / 'summary_present.html', context)

        #    # process the data in form.cleaned_data as required
        #    # ...
        #    # redirect to a new URL:
        #    #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        author = request.user.username
        link = obj.link
        tag_string = RssEntryTagsDataModel.get_author_tag_string(author, link)

        if tag_string:
            form = TagEntryForm(initial={'link' : link, 'author' : author, 'tag' : tag_string})
        else:
            form = TagEntryForm(initial={'link' : link, 'author' : author})

        form.method = "POST"
        form.pk = pk
        form.action_url = reverse('rsshistory:entry-tag', args=[pk])
        context['form'] = form
        context['form_title'] = obj.title
        context['form_description'] = obj.title

    return render(request, get_app() / 'form_basic.html', context)


def tag_remove(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove tag"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    entry = RssEntryTagsDataModel.objects.get(id=pk)
    entry.delete()

    context["summary_text"] = "Remove ok"

    return render(request, get_app() / 'summary_present.html', context)
