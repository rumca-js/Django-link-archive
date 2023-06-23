from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from .models import SourceDataModel, LinkDataModel
from .basictypes import *
from .prjconfig import Configuration
from .apps import LinkDatabase


class ContextData(object):
    # https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
    app_name = Path(LinkDatabase.name)

    def get_full_template(template):
        return ContextData.app_name / "linkdatamodel_list.html"

    def init_context(request, context):
        c = Configuration.get_object()
        context.update(c.get_context())

        from django_user_agents.utils import get_user_agent

        user_agent = get_user_agent(request)
        context["is_mobile"] = user_agent.is_mobile

        return context

    def get_context(request=None):
        context = {}
        context = ContextData.init_context(request, context)
        return context

    def render(request, template, context=None):
        if context is None:
            context = self.get_context(request)

        return render(request, ContextData.app_name / template, context)


def index(request):
    # Generate counts of some of the main objects
    num_sources = SourceDataModel.objects.all().count()
    num_entries = LinkDataModel.objects.all().count()
    num_persistent = LinkDataModel.objects.filter(persistent=True).count()

    context = ContextData.get_context(request)

    context["num_sources"] = num_sources
    context["num_entries"] = num_entries
    context["num_persistent"] = num_persistent

    # Render the HTML template index.html with the data in the context variable
    return ContextData.render(request, "index.html", context=context)
