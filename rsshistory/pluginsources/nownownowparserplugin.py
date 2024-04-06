from django.contrib.auth.models import User

from ..models import UserTags
from ..controllers import BackgroundJobController
from .domainparserplugin import DomainParserPlugin


class NowNowNowParserPlugin(DomainParserPlugin):
    """
    Created for https://nownownow.com/
    """

    PLUGIN_NAME = "NowNowNowParserPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def add_link(self, link_str):
        from ..configuration import Configuration

        c = Configuration.get_object()

        admin_user = User.objects.get(is_superuser=True)

        BackgroundJobController.link_add(link_str, source=self.get_source(), user=admin_user, tag="personal")
