from pathlib import Path

from django.shortcuts import render
from django.views import generic
from django.urls import reverse

from .models import UserConfig
from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
)
from .basictypes import *
from .configuration import Configuration
from .apps import LinkDatabase


class ContextData(object):
    # https://stackoverflow.com/questions/66630043/django-is-loading-template-from-the-wrong-app
    app_name = Path(LinkDatabase.name)

    def get_full_template(template):
        return ContextData.app_name / template

    def init_context(request, context):
        c = Configuration.get_object()
        context.update(c.get_context())

        user_name = request.user.get_username()
        context["user_config"] = UserConfig.get(user_name)

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
    context = ContextData.get_context(request)

    # Render the HTML template index.html with the data in the context variable
    return ContextData.render(request, "index.html", context=context)
