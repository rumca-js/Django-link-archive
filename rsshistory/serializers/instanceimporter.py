import os
import json
import traceback

from django.contrib.auth.models import User

from ..models import Domains, AppLogging, UserBookmarks, UserTags, UserVotes

from ..controllers import (
    LinkDataController,
    SourceDataController,
    SourceDataController,
    EntryDataBuilder,
    SourceDataBuilder,
    LinkCommentDataController,
    EntryWrapper,
)
from ..apps import LinkDatabase
from ..configuration import Configuration
from ..dateutils import DateUtils


class InstanceExporter(object):
    def export_link(self, link):
        link_map = {"link": link.get_map_full()}
        return link_map

    def export_links(self, links):
        json_obj = {"links": []}

        for link in links:
            link_map = link.get_map_full()
            json_obj["links"].append(link_map)

        return json_obj

    def export_source(self, source):
        source_map = {"source": source.get_map_full()}
        return source_map

    def export_sources(self, sources):
        json_obj = {"sources": []}

        for source in sources:
            source_map = source.get_map_full()
            json_obj["sources"].append(source_map)

        return json_obj


class BaseImporter(object):
    def __init__(self, user=None, import_settings=None):
        self.user = user

        if self.user is None:
            self.user = self.get_superuser()

        self.import_settings = import_settings
        if self.import_settings is None:
            self.import_settings = {}
            self.import_settings["import_entries"] = True
            self.import_settings["import_sources"] = True
            self.import_settings["import_title"] = True
            self.import_settings["import_description"] = True
            self.import_settings["import_tags"] = True
            self.import_settings["import_comments"] = True
            self.import_settings["import_votes"] = True
            self.import_settings["import_bookmarks"] = True

    def import_from_json(self, json_data):
        if "links" in json_data:
            return self.import_from_links(json_data["links"])

        elif "sources" in json_data:
            return self.import_from_sources(json_data["sources"])

        elif "link" in json_data:
            return self.import_from_link(json_data["link"])

        elif "source" in json_data:
            return self.import_from_source(json_data["source"])

        elif len(json_data) > 0:
            return self.import_from_list(json_data)

        else:
            raise NotImplementedError()

        return False

    def import_from_list(self, json_data):
        first_item = json_data[0]
        if "link" in first_item:
            return self.import_from_links(json_data)
        elif "url" in first_item:
            return self.import_from_sources(json_data)

        return False

    def import_from_links(self, json_data):
        LinkDatabase.info("Import from links")

        for link_data in json_data:
            try:
                self.import_from_link(link_data)
            except Exception as E:
                AppLogging.exc(E, "Cannot import link data {}".format(link_data))

        return True

    def import_from_sources(self, json_data):
        LinkDatabase.info("Import from sources")

        for source_data in json_data:
            try:
                self.import_from_source(source_data)
            except Exception as E:
                AppLogging.exc(E, "Cannot import source data {}".format(source_data))

        return True

    def copy_props(self, entry, clean_data):
        if self.import_settings and self.import_settings["import_bookmarks"]:
            if "bookmarked" in clean_data:
                entry.bookmarked = clean_data["bookmarked"]
        if "permanent" in clean_data:
            entry.permanent = clean_data["permanent"]
        if self.import_settings and self.import_settings["import_title"]:
            if "title" in clean_data:
                entry.title = clean_data["title"]
        if self.import_settings and self.import_settings["import_description"]:
            if "description" in clean_data:
                entry.description = clean_data["description"]
        if "date_published" in clean_data:
            entry.date_published = clean_data["date_published"]
        entry.save()

    def import_from_link(self, json_data):
        """
        TODO please refactor this function. It is too big
        """
        c = Configuration.get_object().config_entry

        tags = []
        if "tags" in json_data:
            tags = json_data["tags"]
        vote = None
        if "vote" in json_data:
            vote = json_data["vote"]
        comments = []
        if "comments" in json_data:
            comments = json_data["comments"]

        clean_data = self.get_clean_entry_data(json_data)

        entry = None

        entries = LinkDataController.objects.filter(link=clean_data["link"])
        if entries.count() == 0:
            if self.import_settings and self.import_settings["import_entries"]:
                # This instance can have their own settings for import, may decide what is
                # accepted and not. Let the builder deal with it
                LinkDatabase.info("Importing link:{}".format(clean_data["link"]))

                b = EntryDataBuilder(link_data=clean_data, source_is_auto=True)
                entry = b.result

                if entry and entry.is_archive_entry():
                    entry = EntryWrapper.move_from_archive(entry)

                    self.copy_props(entry, clean_data)
        else:
            entry = entries[0]

            self.copy_props(entry, clean_data)

        if entry:
            if self.import_settings and self.import_settings["import_bookmarks"]:
                if entry.bookmarked:
                    UserBookmarks.add(self.user, entry)
                else:
                    UserBookmarks.remove_entry(entry)

            if self.import_settings and self.import_settings["import_tags"]:
                if len(tags) > 0:
                    user = self.get_superuser()
                    for tag in tags:
                        UserTags.set_tag(entry, tag, user)

            if self.import_settings and self.import_settings["import_votes"]:
                if vote is not None:
                    UserVotes.add(self.user, entry, vote)

            if self.import_settings and self.import_settings["import_comments"]:
                if len(comments) > 0:
                    for comment in comments:
                        user = self.get_user(comment["user"])
                        data = {}

                        if entry:
                            data["entry_object"] = entry

                        if user:
                            data["user"] = user

                        data["comment"] = comment["comment"]
                        data["date_published"] = comment["date_published"]
                        data["date_edited"] = comment["date_edited"]
                        data["reply_id"] = comment["reply_id"]
                        LinkCommentDataController.add(user, entry, data)

        return True

    def get_superuser(self):
        users = User.objects.filter(is_superuser=True)
        if users.count() > 0:
            return users[0]

    def get_user(self, username):
        users = User.objects.filter(username=username)
        if users.count() > 0:
            return users[0]

    def import_from_source(self, json_data, instance_import=False):
        LinkDatabase.info("Import from source")

        clean_data = SourceDataController.get_clean_data(json_data)

        sources = SourceDataController.objects.filter(url=clean_data["url"])
        if sources.count() == 0:
            clean_data = self.drop_source_instance_internal_data(clean_data)
            if instance_import:
                clean_data["enabled"] = False
            SourceDataBuilder(link_data=clean_data).add_from_props()
        # TODO cleanup
        # else:
        #    if instance_import:
        #        source = sources[0]

        #        if source.enabled != (not clean_data["enabled"]):
        #            source.enabled = not clean_data["enabled"]

        #        if source.proxy_location != clean_data["proxy_location"]:
        #            source.proxy_location = clean_data["proxy_location"]

        #        source.save()
        return True

    def drop_entry_instance_internal_data(self, clean_data):
        if "domain_obj" in clean_data:
            del clean_data["domain_obj"]
        if "source_obj" in clean_data:
            del clean_data["domain_obj"]
        if "id" in clean_data:
            del clean_data["id"]

        return clean_data

    def drop_source_instance_internal_data(self, clean_data):
        if "dynamic_data" in clean_data:
            del clean_data["dynamic_data"]
        if "id" in clean_data:
            del clean_data["id"]

        return clean_data

    def get_clean_entry_data(self, input_data):
        clean_data = LinkDataController.get_clean_data(input_data)
        clean_data = self.drop_entry_instance_internal_data(clean_data)

        if "date_published" in clean_data:
            clean_data["date_published"] = DateUtils.parse_datetime(
                clean_data["date_published"]
            )

        return clean_data


def get_list_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list


def read_file_contents(file_path):
    """
    TODO use pathlib?
    """
    with open(file_path, "r") as f:
        return f.read()


class FileImporter(BaseImporter):
    def __init__(self, path=None, user=None):
        AppLogging.info("Importing from a file")
        super().__init__(user)

        if not os.path.isdir(path):
            AppLogging.error("Directory does not exist!")
            return

        self.import_from_path(path)

    def import_from_path(self, path):
        files = get_list_files(path)
        for afile in files:
            if afile.endswith(".json"):
                self.import_from_file(afile)

    def import_from_file(self, afile):
        contents = read_file_contents(afile)
        if contents:
            data = json.loads(contents)
            return self.import_from_json(data)

        return False


class InstanceImporter(BaseImporter):
    def __init__(self, url=None, author=None):
        super().__init__(author)
        self.url = url

    def import_all(self):
        from ..pluginurl import UrlHandler

        u = UrlHandler(self.url)
        instance_text = u.get_contents()
        if not instance_text:
            return

        try:
            json_data = json.loads(instance_text)
        except Exception as E:
            exc_string = traceback.format_exc()
            AppLogging.info(
                "Cannot load JSON:{}\nExc:{}".format(instance_text, exc_string)
            )
            return

        if "links" in json_data:
            self.import_from_links(json_data["links"])

            if len(json_data["links"]) > 0:
                url = self.get_next_page_link()
                importer = InstanceImporter(url, self.user)
                importer.import_all()

        elif "sources" in json_data:
            self.import_from_sources(json_data["sources"])

            if len(json_data["sources"]) > 0:
                url = self.get_next_page_link()
                importer = InstanceImporter(url, self.user)
                importer.import_all()

        elif "link" in json_data:
            self.import_from_link(json_data["link"])

        elif "source" in json_data:
            self.import_from_source(json_data["source"])

    def get_next_page_link(self):
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

        parsed_url = urlparse(self.url)
        query_params = parse_qs(parsed_url.query)

        page_param = 0
        if "page" in query_params:
            page_param = query_params["page"][0]

        if page_param is not None:
            try:
                page_param = int(page_param) + 1
            except ValueError:
                page_param = 0
        else:
            page_param = 0

        # Update the 'page' parameter in the query string
        query_params["page"] = [str(page_param)]

        # Construct the new URL
        new_query_string = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=new_query_string))

        return new_url
