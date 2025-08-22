from datetime import timedelta
import os
import traceback
import time

from django.db import models
from django.urls import reverse
from django.db.models import Q

from utils.dateutils import DateUtils

from ..models import (
    LinkDataModel,
    ArchiveLinkDataModel,
    ReadMarkers,
)
from ..configuration import Configuration
from ..apps import LinkDatabase


class LinkDataController(LinkDataModel):
    class Meta:
        proxy = True

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""
        if self.is_archive_entry():
            return reverse(
                "{}:entry-archive-detail".format(LinkDatabase.name), args=[str(self.id)]
            )
        else:
            return reverse(
                "{}:entry-detail".format(LinkDatabase.name), args=[str(self.id)]
            )

    def get_edit_url(self):
        """Returns the URL to access a particular author instance."""

        return reverse("{}:entry-edit".format(LinkDatabase.name), args=[str(self.id)])

    def get_bookmark_set_url(self):
        """Returns the URL to access a particular author instance."""
        if self.is_archive_entry():
            return reverse(
                "{}:entry-archive-bookmark".format(LinkDatabase.name),
                args=[str(self.id)],
            )
        else:
            return reverse(
                "{}:json-entry-bookmark".format(LinkDatabase.name), args=[str(self.id)]
            )

    def get_bookmark_unset_url(self):
        """Returns the URL to access a particular author instance."""
        if self.is_archive_entry():
            return reverse(
                "{}:entry-archive-unbookmark".format(LinkDatabase.name),
                args=[str(self.id)],
            )
        else:
            return reverse(
                "{}:json-entry-unbookmark".format(LinkDatabase.name), args=[str(self.id)]
            )

    def get_dead_url(self):
        if self.is_dead():
            """Returns the URL to access a particular author instance."""
            return reverse(
                "{}:entry-not-dead".format(LinkDatabase.name), args=[str(self.id)]
            )
        else:
            return reverse(
                "{}:entry-dead".format(LinkDatabase.name), args=[str(self.id)]
            )

    def get_title_safe(self):
        title = self.title
        if title:
            title = title.replace('"', "")
            title = title.replace("'", "")

        return title

    def get_search_term(self):
        term = ""

        title = self.get_title_safe()
        if title and title != "":
            if term != "":
                term += " "
            term += title

        if self.album and self.album != "" and term.find(self.album) == -1:
            term = self.album + " " + term

        if self.author and self.author != "" and term.find(self.author) == -1:
            term = self.author + " " + term

        term.strip()

        return term

    def get_remove_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse("{}:entry-remove".format(LinkDatabase.name), args=[str(self.id)])

    def cleanup(cfg=None):
        """
        We do not want to starve other threads.
        Add limit, so that we can exit from cleanup thread
        """

        cleanup = EntriesCleanup(archive_cleanup=False)
        cleanup.cleanup()
        cleanup = EntriesCleanup(archive_cleanup=True)
        cleanup.cleanup()

        # TODO Move to link wrapper
        moved_all = EntryWrapper.move_old_links_to_archive(limit_s)

        LinkDataController.update_entries()

        # indicate that all has been finished correctly
        return moved_all

    def truncate(cfg=None):
        BATCH_SIZE = 1000

        entries = LinkDataController.objects.all()

        if entries.exists():
            entries[:BATCH_SIZE].delete()

    def get_full_information(data):
        from ..pluginurl.entryurlinterface import EntryUrlInterface

        info = EntryUrlInterface(data["link"], log=True, ignore_errors=True).get_props()
        info["page_rating_votes"] = 0

        return info

    def get_clean_data(props):
        from ..pluginurl import UrlHandlerEx

        result = {}
        test = LinkDataController()

        for key in props:
            if hasattr(test, key):
                result[key] = props[key]

        result = LinkDataController.get_clean_field(result, "link")
        result = LinkDataController.get_clean_field(result, "title")
        result = LinkDataController.get_clean_field(result, "description")
        result = LinkDataController.get_clean_field(result, "author")
        result = LinkDataController.get_clean_field(result, "album")

        if "link" in result:
            result["link"] = UrlHandlerEx.get_cleaned_link(result["link"])

        if "tags" in result:
            del result["tags"]
        if "comments" in result:
            del result["comments"]
        if "vote" in result:
            del result["vote"]

        return result

    def get_clean_field(props, field):
        if field in props and props[field]:
            props[field] = props[field].replace("\0", "")

        return props

    def vote(self, vote):
        self.page_rating_votes = vote
        self.save()

    def is_archive_time(self):
        conf = Configuration.get_object().config_entry
        if conf.days_to_move_to_archive == 0:
            return False

        day_to_move = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_move_to_archive
        )

        if self.date_published and self.date_published < day_to_move:
            return True

        if self.date_created and self.date_created < day_to_move:
            return True

        return False

    def is_remove_time(self):
        conf = Configuration.get_object().config_entry
        if conf.days_to_remove_links == 0:
            return False

        day_to_remove = DateUtils.get_datetime_now_utc() - timedelta(
            days=conf.days_to_remove_links
        )

        if not self.date_published:
            return self.date_created < day_to_remove

        return self.date_published < day_to_remove

    def is_bookmarked(self):
        from ..models import UserBookmarks

        return UserBookmarks.is_bookmarked(self)


class ArchiveLinkDataController(ArchiveLinkDataModel):
    """
    Normal operation database is for optimization.
    Rest of data go into archive. Archive should behave just as normal archive
    """

    class Meta:
        proxy = True

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""

        return reverse(
            "{}:entry-archived".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_edit_url(self):
        """Returns the URL to access a particular author instance."""

        return reverse(
            "{}:entry-archive-edit".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_bookmark_set_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-bookmark".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_bookmark_unset_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-notbookmark".format(LinkDatabase.name),
            args=[str(self.id)],
        )

    def get_hide_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-hide".format(LinkDatabase.name), args=[str(self.id)]
        )

    def get_remove_url(self):
        """Returns the URL to access a particular author instance."""
        return reverse(
            "{}:entry-archive-remove".format(LinkDatabase.name), args=[str(self.id)]
        )

    def is_bookmarked(self):
        return False

    def truncate(cfg=None):
        BATCH_SIZE = 1000

        entries = ArchiveLinkDataController.objects.all()

        if entries.exists():
            entries[:BATCH_SIZE].delete()
