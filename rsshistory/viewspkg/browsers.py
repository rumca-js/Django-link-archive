from ..models import Browser
from ..controllers import (
    LinkDataController,
)
from ..models import ConfigurationEntry, Browser
from ..views import ViewPage, GenericListView


class BrowserListView(GenericListView):
    model = Browser
    context_object_name = "content_list"
    paginate_by = 100


def apply_browser_setup(request):
    p = ViewPage(request)
    p.set_title("Clear entire later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    Browser.apply_browser_setup()

    p.context["summary_text"] = "OK"
    return p.render("go_back.html")


def read_browser_setup(request):
    p = ViewPage(request)
    p.set_title("Clear entire later list")
    data = p.set_access(ConfigurationEntry.ACCESS_TYPE_ALL)
    if data is not None:
        return data

    Browser.read_browser_setup()

    p.context["summary_text"] = "OK"
    return p.render("go_back.html")
