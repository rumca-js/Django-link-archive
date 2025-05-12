from utils.dateutils import DateUtils

from ..models import AppLogging, UserTags
from ..controllers import EntryDataBuilder, SourceDataController
from ..configuration import Configuration


class SourcePluginInterface(object):
    """
    Class names schemes:
     - those that are ancestors, and generic use "Base" class prefix
     - file names start with source, because I did not know if they will not be in one place
       with entries, so I wanted to be able to distinguish them later
    """

    PLUGIN_NAME = ""

    def __init__(self, source_id, options=None):
        self.source_id = source_id
        self.dead = False
        self.num_read_entries = 0
        self.start_time = None

    def check_for_data(self):
        self.num_read_entries = 0

        source = self.get_source()
        if not source.enabled:
            return

        AppLogging.debug("Starting processing source:{}".format(source.url))

        # We do not check if data is correct. We can manually add processing to queue
        # We want the source to be processed then

        self.start_time = DateUtils.get_datetime_now_utc()

        self.hash = self.get_hash()

        if source:
            source.update_data()

        self.read_entries()

        stop_time = DateUtils.get_datetime_now_utc()
        total_time = stop_time - self.start_time
        total_time.total_seconds()

        AppLogging.debug("Stopping processing source:{}".format(source.url))

        self.set_operational_info(
            stop_time, self.num_read_entries, total_time.total_seconds(), self.hash
        )

    def read_entries(self):
        pass

    def get_source(self):
        sources = SourceDataController.objects.filter(id=self.source_id)
        if sources.exists():
            return sources[0]

    def get_hash(self):
        pass

    def set_operational_info(
        self, stop_time, num_entries, total_seconds, hash_value, valid=True
    ):
        source = self.get_source()

        source.set_operational_info(
            stop_time, num_entries, total_seconds, hash_value, valid
        )

    def enhance_properties(self, properties):
        source = self.get_source()

        if source:
            if (
                self.is_property_set(properties, "language")
                and source.language != None
                and source.language != ""
            ):
                properties["language"] = source.language

            properties["source_url"] = source.url
            properties["source"] = source
            if source.age > 0:
                properties["age"] = source.age

        if "page_rating" in properties:
            properties["page_rating_contents"] = properties["page_rating"]

        return properties

    def on_added_entry(self, entry):
        if not entry:
            return

        source = self.get_source()

        if entry and (entry.date_created > self.start_time):
            if source.auto_tag:
                user = Configuration.get_object().get_superuser()
                UserTags.set_tag(entry, source.auto_tag, user)

        self.num_read_entries += 1

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
