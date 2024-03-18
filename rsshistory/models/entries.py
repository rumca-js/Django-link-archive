from datetime import datetime, date, timedelta

from django.db import models
from django.urls import reverse
from django.templatetags.static import static
from django.utils import timezone
import traceback

from ..apps import LinkDatabase
from ..webtools import HtmlPage

from .sources import SourceDataModel
from .system import AppLogging
from .domains import Domains


class BaseLinkDataModel(models.Model):
    link = models.CharField(max_length=1000, unique=True)

    # URL of source, might be RSS source
    source = models.CharField(max_length=2000)

    title = models.CharField(max_length=1000, null=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    thumbnail = models.CharField(max_length=1000, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    age = models.IntegerField(blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_published = models.DateTimeField(default=timezone.now)
    date_update_last = models.DateTimeField(auto_now=True, null=True)
    date_dead_since = models.DateTimeField(null=True)

    # this entry cannot be removed. Serves a purpose. Domain page, source page
    permanent = models.BooleanField(default=False)
    bookmarked = models.BooleanField(default=False)
    dead = models.BooleanField(default=False)

    # user who added entry
    user = models.CharField(max_length=1000, null=True, blank=True)

    # We could use a different model, but it may lead to making multiple queries
    # For each model.

    # Archive was introduced to have two tables:
    #  - link model (fast)
    #  - archive (slow)

    # If we have moved artist & album to one big table, then it would go against this
    # solution.
    # We do not want to have archive tables for everything.

    artist = models.CharField(max_length=1000, null=True, blank=True)
    album = models.CharField(max_length=1000, null=True, blank=True)

    status_code = models.IntegerField(default=0)

    page_rating_contents = models.IntegerField(default=0)
    page_rating_votes = models.IntegerField(default=0)
    page_rating_visits = models.IntegerField(default=0)
    page_rating = models.IntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["-date_published", "source", "title"]


class BaseLinkDataController(BaseLinkDataModel):
    class Meta:
        abstract = True
        ordering = ["-date_published", "source", "title"]

    def get_absolute_url(self):
        """Returns the URL to access a particular author instance."""

        if self.is_archive_entry():
            return reverse(
                "{}:entry-archived".format(LinkDatabase.name), args=[str(self.id)]
            )
        else:
            return reverse(
                "{}:entry-detail".format(LinkDatabase.name), args=[str(self.id)]
            )

    def get_source_name(self):
        if self.get_source_obj():
            return self.get_source_obj().title
        else:
            return self.source

    def get_link_dead_text(self):
        return "______"

    def get_title(self):
        if self.dead:
            return self.get_link_dead_text()
        return self.title

    def get_long_description(self):
        if self.dead:
            return self.get_link_dead_text()
        return "{} {}".format(self.date_published, self.get_source_name())

    def has_tags(self):
        try:
            if not getattr(self, "tags"):
                return 0
        except Exception as E:
            return 0

        return len(self.tags.all()) > 0

    def get_full_description(self):
        if self.dead:
            return self.get_link_dead_text()
        string = self.get_long_description()

        tags = self.get_tag_string()
        if tags:
            string += " Tags:{}".format(tags)
        if self.user:
            string += " User:{}".format(self.user)

        return string

    def get_tag_string(self):
        try:
            from .models import LinkTagsDataModel

            return LinkTagsDataModel.join_elements(self.tags.all())
        except Exception as e:
            return ""

    def get_vote(self):
        return self.page_rating_votes

    def calculate_vote(self):
        if not self.is_taggable():
            return 0
        try:
            if not getattr(self, "votes"):
                return 0
        except Exception as E:
            return 0

        votes = self.votes.all()
        count = votes.count()
        if count == 0:
            return 0

        sum_num = 0
        for vote in votes:
            sum_num += vote.vote

        return sum_num / count

    def get_visits(self):
        from .userhistory import UserEntryVisitHistory

        visits = UserEntryVisitHistory.objects.filter(entry_object=self)

        sum_num = 0
        for visit in visits:
            sum_num += visit.visits

        return sum_num

    def update_data(self):
        """
        Fetches new information about page, and uses valid fields to set this object,
        but only if current field is not set

         - status code and page rating is update always
         - title and description could have been set manually, we do not want to change that
         - some other fields should be set only if present in props
        """
        if self.dead or self.page_rating_votes < 0:
            AppLogging.warning("Cannot update link that is dead")
            return

        from ..pluginurl.entryurlinterface import EntryUrlInterface

        url = EntryUrlInterface(self.link)
        props = url.get_props()
        p = url.p

        # always update
        self.page_rating_contents = p.get_page_rating()
        self.status_code = p.status_code

        if not props:
            self.save()
            return

        if "title" in props and props["title"] is not None:
            if not self.title:
                self.title = props["title"]

        if "description" in props and props["description"] is not None:
            if not self.description:
                self.description = props["description"]

        if "thumbnail" in props and props["thumbnail"] is not None:
            if not self.thumbnail:
                self.thumbnail = props["thumbnail"]

        if "language" in props and props["language"] is not None:
            if not self.language:
                self.language = props["language"]

        if "date_published" in props and props["date_published"] is not None:
            if not self.date_published:
                self.date_published = props["date_published"]

        self.update_calculated_vote()

    def reset_data(self):
        """
        Fetches new information about page, and uses valid fields to set this object.

         - status code and page rating is update always
         - new data are changed only if new data are present at all
        """
        if self.dead or self.page_rating_votes < 0:
            AppLogging.warning("Cannot update link that is dead")
            return

        from ..pluginurl.entryurlinterface import EntryUrlInterface

        url = EntryUrlInterface(self.link)
        props = url.get_props()

        self.page_rating_contents = url.p.get_page_rating()
        self.status_code = url.p.status_code

        if not props:
            self.save()
            return

        if "title" in props and props["title"] is not None:
            self.title = props["title"]

        if "description" in props and props["description"] is not None:
            self.description = props["description"]

        if "thumbnail" in props and props["thumbnail"] is not None:
            self.thumbnail = props["thumbnail"]

        if "language" in props and props["language"] is not None:
            self.language = props["language"]

        # if "date_published" in props and props["date_published"] is not None:
        #    self.date_published = props["date_published"]

        self.save()

    def update_calculated_vote(self):
        self.page_rating_votes = self.calculate_vote()
        self.page_rating_visits += self.get_visits()
        self.page_rating = self.page_rating_votes + self.page_rating_contents
        self.save()

    def get_tag_map(self):
        # TODO should it be done by for tag in self.tags: tag.get_map()?
        result = []

        if not self.is_taggable():
            return result

        tags = self.tags.all()
        for tag in tags:
            result.append(tag.tag)
        return result

    def get_comment_vec(self):
        result = []

        comments = self.comments.all()
        for comment in comments:
            data = {}
            data["comment"] = comment.comment
            data["user"] = comment.user_object.username
            data["date_published"] = comment.date_published.isoformat()
            data["date_edited"] = comment.date_published.isoformat()
            data["reply_id"] = comment.reply_id
            result.append(data)

        return result

    def update_language(self):
        if self.get_source_obj():
            self.language = self.get_source_obj().language
            self.save()
        else:
            page = HtmlPage(self.link)
            if page.is_valid():
                language = page.get_language()
                if language != None:
                    self.language = language
                    self.save()

    def get_favicon(self):
        """
        Prints favicon from source, or from HTML page directly
        """
        if self.age and self.age >= 18:
            return static("{0}/images/sign-304093_640.png".format(LinkDatabase.name))

        if self.get_source_obj():
            return self.get_source_obj().get_favicon()

        from ..webtools import BasePage

        # returning real favicon from HTML is too long
        return BasePage(self.link).get_domain() + "/favicon.ico"

    def get_domain_only(self):
        from ..webtools import BasePage

        page = BasePage(self.link)
        return page.get_domain_only()

    def get_thumbnail(self):
        """
        Prints thumbnail, but if it does not have one prints favicon
        """
        if self.age and self.age >= 18:
            return static("{0}/images/sign-304093_640.png".format(LinkDatabase.name))

        if self.thumbnail:
            return self.thumbnail

        return self.get_favicon()

    def get_export_names():
        """
        Provides object export names. No dependencies towards other objects
        """
        return [
            "source",
            "title",
            "description",
            "link",
            "date_published",
            "permanent",
            "bookmarked",
            "dead",
            "artist",
            "album",
            "user",
            "language",
            "thumbnail",
            "age",
            "page_rating_contents",
            "page_rating_votes",
            "page_rating_visits",
            "page_rating",
        ]

    def get_query_names():
        names = set(BaseLinkDataController.get_export_names())
        names.add("source_obj__id")
        names.add("source_obj__url")
        names.add("source_obj__title")
        names.add("source_obj__category")
        names.add("source_obj__subcategory")
        names.add("tags__tag")
        names.add("votes__vote")
        return list(names)

    def get_all_export_names():
        """
        Provides object export names with dependencies from other objects
        """
        names = set(BaseLinkDataController.get_export_names())
        names.add("source_obj__id")
        names.add("tags")
        names.add("comments")
        names.add("vote")
        return list(names)

    def get_map(self):
        output_data = {}

        export_names = BaseLinkDataController.get_export_names()
        for export_name in export_names:
            val = getattr(self, export_name)
            if export_name.find("date_") >= 0:
                val = val.isoformat()
            output_data[export_name] = val

        return output_data

    def get_map_full(self):
        themap = self.get_map()

        tags = self.get_tag_map()
        if len(tags) > 0:
            themap["tags"] = tags
        else:
            themap["tags"] = []

        vote = self.get_vote()
        if vote > 0:
            themap["vote"] = vote
        else:
            themap["vote"] = 0

        comments = self.get_comment_vec()
        if len(comments) > 0:
            themap["comments"] = comments
        else:
            themap["comments"] = []

        if self.source_obj:
            themap["source_obj__id"] = self.source_obj.id

        return themap

    def get_archive_link(self):
        from ..services.waybackmachine import WaybackMachine
        from ..dateutils import DateUtils

        m = WaybackMachine()
        formatted_date = m.get_formatted_date(self.date_published.date())
        archive_link = m.get_archive_url_for_date(formatted_date, self.link)
        return archive_link

    def make_bookmarked(self):
        self.bookmarked = True
        self.permanent = True
        self.save()

    def make_not_bookmarked(self):
        from ..models import UserTags, UserVotes

        self.permanent = False

        # TODO code below I think is not necessary, as entry_object link is cascade

        tags = UserTags.objects.filter(entry_object=self)
        tags.delete()

        votes = UserVotes.objects.filter(entry_object=self)
        votes.delete()

        self.bookmarked = False
        self.save()

    def make_dead(self, state):
        from ..dateutils import DateUtils

        if not self.dead and state:
            self.date_dead_since = DateUtils.get_datetime_now_utc()
            self.page_rating_contents = 0
            # remove all tags & comments?
        elif self.dead and not state:
            self.date_dead_since = None

        self.dead = state
        self.save()

    def is_taggable(self):
        return (self.permanent or self.bookmarked) and self.page_rating_votes >= 0

    def is_commentable(self):
        return (self.permanent or self.bookmarked) and self.page_rating_votes >= 0

    def is_valid(self):
        """
        Link is not valid:
         - if status indicates so
         - if it is dead (manual indication)
         - if it was downvoted to oblivion
        """
        return self.is_status_code_valid() and self.page_rating > 0 and not self.dead

    def is_status_code_valid(self):
        if self.status_code == 403:
            # Many pages return 403, but they are correct
            return True

        if self.status_code == 0:
            # The page has not yet been fetched / checked
            return True

        return self.status_code >= 200 and self.status_code < 300

    def is_archive_entry(self):
        """
        TODO: change to is_archive()
        """
        return False

    def is_archive_by_date(input_date):
        from ..dateutils import DateUtils
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry
        if conf.days_to_move_to_archive == 0:
            return False

        date_to_move = DateUtils.get_days_before_dt(conf.days_to_move_to_archive)

        if input_date < date_to_move:
            return True
        return False

    def get_description_safe(description):
        if not description or description == "":
            return description

        length = BaseLinkDataController.get_description_length()
        return description[: length - 10]

    def get_description_length():
        return 1000


class LinkDataModel(BaseLinkDataController):
    source_obj = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="link_source",
        null=True,
        blank=True,
    )
    domain_obj = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class ArchiveLinkDataModel(BaseLinkDataController):
    source_obj = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="archive_source",
        null=True,
        blank=True,
    )
    domain_obj = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    def is_archive_entry(self):
        return True
