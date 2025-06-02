from utils.services import EmailReader
from utils.dateutils import DateUtils

from ..controllers import EntryDataBuilder
from ..configuration import Configuration
from ..models import AppLogging

from .sourceplugininterface import SourcePluginInterface


class EmailSourcePlugin(SourcePluginInterface):
    """
    Class names schemes:
     - those that are ancestors, and generic use "Base" class prefix
     - file names start with source, because I did not know if they will not be in one place
       with entries, so I wanted to be able to distinguish them later
    """

    PLUGIN_NAME = "EmailSourcePlugin"

    def __init__(self, source_id, options=None):
        super().__init__(source_id=source_id, options=options)

    def read_entries(self):
        source = self.get_source()
        if not source.credentials:
            AppLogging.error(
                "Source:{} Credentials were not defined for source.".format(source.id)
            )
            return

        day_to_remove = Configuration.get_object().get_entry_remove_date()

        try:
            reader = EmailReader(source.url, time_limit=day_to_remove)
            credentials = source.credentials
            credentials.decrypt()

            if not reader.connect(credentials.username, credentials.password):
                AppLogging.error(
                    "Source:{} Could not login to service.".format(source.id)
                )
                return
        except socket.gaierror as E:
            AppLogging.exc(E, "Source:{} Email exception.".format(source.id))
            return

        for email in reader.get_emails():
            self.on_email(email)

    def on_email(self, email):
        link_data = {}
        link_data["title"] = email.title
        link_data["date_published"] = DateUtils.to_utc_date(email.date_published)
        link_data["description"] = email.body
        link_data["author"] = email.author
        link_data["link"] = self.get_entry_link(email)

        link_data = self.enhance_properties(link_data)

        b = EntryDataBuilder()
        entry = b.build(link_data=link_data, source_is_auto=True)

        self.on_added_entry(entry)

    def get_entry_link(self, email):
        source = self.get_source()
        return "email://{}/{}/{}".format(source.url, source.username, email.id)
