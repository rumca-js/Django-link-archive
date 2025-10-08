from django.db import models
from django.db.models import Q, F

from webtoolkit import UrlLocation

from ..models import (
    BaseLinkDataController,
    AppLogging,
    UserBookmarks,
)
from ..configuration import Configuration
from ..apps import LinkDatabase
from .entries import LinkDataController, ArchiveLinkDataController


class EntryWrapper(object):
    """
    Wrapper for entry. Entries can reside in many places (operation table, archive table).
    This is unified API for them.

    Provides API to make links more uniform (http vs https)
    """

    def __init__(self, link=None, date=None, entry=None, user=None, strict_ids=False):
        """
        if strict_ids is true, then we use link_data "ids"
        """
        self.date = date
        self.entry = entry
        self.user = user
        self.strict_ids = strict_ids

        self.link = None
        if self.entry:
            self.link = self.entry.link
        if link:
            self.link = link

        if date is None:
            if self.entry:
                self.date = self.entry.date_published

    def get(self):
        """
        returns object from any relevant table: operation, archive
        """
        ob = self.get_internal()
        self.entry = ob
        return ob

    def get_internal(self):
        config = Configuration.get_object().config_entry
        if config.days_to_move_to_archive == 0:
            return self.get_from_db(LinkDataController.objects)

        if not self.link:
            return

        if self.date:
            is_archive = self.is_archive()

            if not is_archive:
                obj = self.get_from_db(LinkDataController.objects)
                if obj:
                    return obj
            else:
                obj = self.get_from_db(ArchiveLinkDataController.objects)
                if obj:
                    return obj

        else:
            obj = self.get_from_db(LinkDataController.objects)
            if obj:
                return obj

            obj = self.get_from_db(ArchiveLinkDataController.objects)
            if obj:
                return obj

    def get_from_db(self, objects):
        if self.link.startswith("http"):
            p = UrlLocation(self.link)

            """
            If there are links with www. at front, and without it, return the one without it
            """
            if p.get_domain_only().startswith("www."):
                link_url = p.get_protocol_url("https")
                link_url = link_url.replace("www.", "")
                entry_objs = objects.filter(link=link_url)

                if entry_objs.exists() and not entry_objs[0].is_dead():
                    return entry_objs[0]

                link_url = p.get_protocol_url("http")
                link_url = link_url.replace("www.", "")
                entry_objs = objects.filter(link=link_url)

                if entry_objs.exists() and not entry_objs[0].is_dead():
                    return entry_objs[0]

            link_https = p.get_protocol_url("https")
            https_objs = objects.filter(link=link_https)

            if https_objs.exists() and not https_objs[0].is_dead():
                return https_objs[0]

            link_http = p.get_protocol_url("http")
            http_objs = objects.filter(link=link_http)

            if http_objs.exists() and not http_objs[0].is_dead():
                return http_objs[0]

            """
            If both are dead - return https
            """

            if https_objs.exists():
                return https_objs[0]
            if http_objs.exists():
                return http_objs[0]

        objs = objects.filter(link=self.link)
        if objs.exists():
            return objs[0]

    def create(self, link_data):
        if "date_published" in link_data:
            self.date = link_data["date_published"]
        else:
            self.date = None

        is_archive = False
        if self.date:
            is_archive = self.is_archive()

        if "bookmarked" in link_data and link_data["bookmarked"]:
            is_archive = False
        if "permanent" in link_data and link_data["permanent"]:
            is_archive = False

        if (
            "language" in link_data
            and link_data["language"]
            and len(link_data["language"]) > 9
        ):
            AppLogging.error(
                "Language setting too long for:{} {}".format(
                    link_data["link"], link_data["language"]
                )
            )
            link_data["language"] = None

        title_length = LinkDataController.get_field_length("title")
        description_length = LinkDataController.get_field_length("description")

        if (
            "title" in link_data
            and link_data["title"]
            and len(link_data["title"]) > title_length - 1
        ):
            link_data["title"] = link_data["title"][: title_length - 1]
        if (
            "description" in link_data
            and link_data["description"]
            and len(link_data["description"]) > description_length - 1
        ):
            link_data["description"] = link_data["description"][
                : description_length - 1
            ]

        if not self.strict_ids and "id" in link_data:
            del link_data["id"]

        if self.user:
            link_data["user"] = self.user

        if not is_archive or self.date is None:
            if self.strict_ids and "id" in link_data:
                objs = LinkDataController.objects.filter(id=link_data["id"])
                if objs.exists():
                    return

            try:
                ob = LinkDataController.objects.create(**link_data)
            except Exception as E:
                AppLogging.exc(E, "Cannot create link {}".format(link_data))
                raise

        elif is_archive:
            if self.strict_ids and "id" in link_data:
                objs = ArchiveLinkDataController.objects.filter(id=link_data["id"])
                if objs.exists():
                    return

            try:
                ob = ArchiveLinkDataController.objects.create(**link_data)
            except Exception as E:
                AppLogging.exc(E, "Cannot create archive link {}".format(link_data))
                raise

        return ob

    def move_to_archive(self):
        entry_obj = self.entry
        link = entry_obj.link

        objs = ArchiveLinkDataController.objects.filter(link=entry_obj.link)

        if not objs.exists():
            themap = entry_obj.get_map(stringify=False)
            try:
                if hasattr(entry_obj, "source"):
                    if entry_obj.source:
                        themap["source"] = entry_obj.source
            except Exception as E:
                AppLogging.exc(E)

            try:
                if hasattr(entry_obj, "domain"):
                    if entry_obj.domain:
                        themap["domain"] = entry_obj.domain
            except Exception as E:
                AppLogging.exc(E)

            if "id" in themap:
                del themap["id"]

            archive_obj = ArchiveLinkDataController.objects.create(**themap)
            entry_obj.delete()
            return archive_obj
        else:
            entry_obj.delete()

    def move_from_archive(self):
        archive_obj = self.entry
        link = archive_obj.link

        objs = LinkDataController.objects.filter(link=archive_obj.link)
        if not objs.exists():
            themap = archive_obj.get_map(stringify=False)
            try:
                if hasattr(archive_obj, "source"):
                    if archive_obj.source:
                        themap["source"] = archive_obj.source
            except Exception as E:
                AppLogging.exc(E)
            try:
                if hasattr(archive_obj, "domain"):
                    if archive_obj.domain:
                        themap["domain"] = archive_obj.domain
            except Exception as E:
                AppLogging.exc(E)
            new_obj = LinkDataController.objects.create(**themap)
            archive_obj.delete()
            return new_obj
        else:
            archive_obj.delete()

    def make_bookmarked(self, request):
        """
        TODO move this API to UserBookmarks
        """
        entry = self.entry

        if entry.is_archive_entry():
            entry = self.move_from_archive()
            if not entry:
                AppLogging.error("Coult not move from archive")
                return

        if UserBookmarks.add(request.user, entry):
            entry.make_bookmarked()

        return entry

    def make_not_bookmarked(self, request):
        entry = self.entry

        UserBookmarks.remove(request.user, entry)

        if not UserBookmarks.is_bookmarked(entry):
            entry.make_not_bookmarked()
            self.evaluate()

        return entry

    def evaluate(self):
        """
        TODO rename to update()

        Checks:
         - if entry should be removed due to config accept_domain_links
         - updates permanent
         - if entry should be moved to archive
        """
        config = Configuration.get_object().config_entry

        entry = self.entry
        if not entry:
            return

        p = UrlLocation(entry.link)
        is_domain = p.is_domain()

        if not entry.should_entry_be_permanent():
            entry.permanent = False
        else:
            entry.permanent = True
        entry.save()

        if is_domain and not config.accept_domain_links:
            if entry.is_removable():
                entry.delete()
                self.entry = None
                return

        if not is_domain and not config.accept_non_domain_links:
            if entry.is_removable():
                entry.delete()
                self.entry = None
                return

        if entry.is_remove_time():
            if entry.is_removable():
                entry.delete()
                self.entry = None
                return

        if not entry.is_permanent() and entry.is_archive_time():
            return self.move_to_archive()

    def move_entry(self, destination_entry):
        """
        Moves entry to destination entry. Both objects need to exist.

        All properties are moved from source entry to destination entry.
        Source entry is destroyed
        """
        if self.entry is None:
            return

        if destination_entry.is_dead():
            return None

        from ..models import (
            UserTags,
            UserVotes,
            UserComments,
            UserBookmarks,
            UserEntryVisitHistory,
            UserEntryTransitionHistory,
        )

        source_entry = self.entry

        UserTags.move_entry(source_entry, destination_entry)
        UserVotes.move_entry(source_entry, destination_entry)
        UserComments.move_entry(source_entry, destination_entry)
        UserBookmarks.move_entry(source_entry, destination_entry)
        UserEntryVisitHistory.move_entry(source_entry, destination_entry)
        UserEntryTransitionHistory.move_entry(source_entry, destination_entry)

        source_entry.delete()
        self.entry = destination_entry

        return self.entry

    def move_entry_to_url(self, destination_url):
        """
        Moves entry to destination url.
        """
        destination_entries = LinkDataController.objects.filter(link=destination_url)

        if destination_entries.exists():
            return self.move_entry(destination_entries[0])
        else:
            self.entry.link = destination_url
            self.entry.save()

            return self.entry

    def is_archive(self):
        is_archive = BaseLinkDataController.is_archive_by_date(self.date)

        return is_archive

    def is_current_entry_perfect(self):
        from ..pluginurl import UrlHandlerEx, EntryUrlInterface

        entry = self.entry

        if not entry:
            return False

        if entry.is_https():
            if entry.link.startswith("https://www"):
                return False

            ping_status = UrlHandlerEx.ping(entry.link)

            return ping_status

    def check_https_http_availability(self):
        """
        We verify if http site also has properties. Sometime non-www pages return 200 status, but are blank
        TODO we do not want to fetch url interface each function like that

        @returns new object, or None object has not been changed
        """
        from ..pluginurl import UrlHandlerEx, EntryUrlInterface

        if not self.entry:
            return

        self.check_https_http_availability_entries()

        entry = self.entry

        c = Configuration.get_object().config_entry
        if not c.prefer_https_links:
            return

        if entry.is_https():
            http_url = entry.get_http_url()

            ping_status = UrlHandlerEx.ping(entry.link)

            if not ping_status:
                url = EntryUrlInterface(http_url)
                props = url.get_props()

                if url.is_valid() and props:
                    return EntryWrapper(entry=entry).move_entry_to_url(http_url)

            return self.entry

        if entry.is_http():
            https_url = entry.get_https_url()

            url = EntryUrlInterface(https_url)
            props = url.get_props()

            if url.is_valid() and props:
                return EntryWrapper(entry=entry).move_entry_to_url(https_url)

        return self.entry

    def check_www_nonww_availability(self):
        """
        We verify if non-www site also has properties. Sometime non-www pages return 200 status, but are blank
        TODO we do not want to fetch url interface each function like that

        @returns new object, or None if object has not been changed
        """
        from ..pluginurl import EntryUrlInterface

        if not self.entry:
            return

        self.check_www_nonww_availability_entries()

        c = Configuration.get_object().config_entry

        if not c.prefer_non_www_links:
            return

        entry = self.entry
        p = UrlLocation(entry.link)
        domain_only = p.get_domain_only()
        if not domain_only.startswith("www."):
            return self.entry

        destination_link = entry.link.replace("www.", "")

        url = EntryUrlInterface(destination_link)
        props = url.get_props()
        if url.is_valid() and props:
            return self.move_entry_to_url(destination_link)

        return self.entry

    def check_https_http_availability_entries(self):
        """
        Removes http<>https duplicates, if we have http and https pages select https to be present
        """
        entry = self.entry

        if entry.is_https():
            http_url = entry.get_http_url()

            http_entries = LinkDataController.objects.filter(link=http_url)
            if http_entries.exists():
                w = EntryWrapper(entry=http_entries[0])
                w.move_entry(entry)

        if entry.is_http():
            https_url = entry.get_https_url()

            # if we have both, destroy http entry
            https_entries = LinkDataController.objects.filter(link=https_url)
            if https_entries.exists():
                self.move_entry(https_entries[0])

        return self.entry

    def check_www_nonww_availability_entries(self):
        """
        Removes non-www and www pages duplicates.
        """
        entry = self.entry

        p = UrlLocation(entry.link)

        url_parts = p.parse_url()
        domain_only = url_parts[2].lower()

        if domain_only.startswith("www."):
            link_with_www = entry.link
            link_without_www = entry.link.replace("www.", "")
        else:
            # TODO should there be API for that?
            link_without_www = entry.link
            joined = "/".join(url_parts[1:])
            link_with_www = url_parts[0] + "www." + joined

        if domain_only.startswith("www."):
            entries = LinkDataController.objects.filter(link=link_without_www)
            if entries.exists():
                self.move_entry(entries[0])
        else:
            entries = LinkDataController.objects.filter(link=link_with_www)
            if entries.exists():
                self.move_entry(self.entry)
