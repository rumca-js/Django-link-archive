from datetime import datetime, date, timedelta

from django.db import models
from django.urls import reverse
from django.templatetags.static import static
from django.utils import timezone

from ..apps import LinkDatabase
from .sources import SourceDataModel
from .admin import PersistentInfo


class BaseLinkDataModel(models.Model):
    link = models.CharField(max_length=1000, unique=True)

    # URL of source, might be RSS source
    source = models.CharField(max_length=2000)

    title = models.CharField(max_length=1000, null=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    thumbnail = models.CharField(max_length=1000, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    age = models.IntegerField(blank=True, null=True)

    date_published = models.DateTimeField(default=timezone.now)
    date_update_last = models.DateTimeField(auto_now=True, null=True)
    date_dead_since = models.DateTimeField(null=True)

    # this entry cannot be removed. Serves a purpose. Domain page, source page
    permanent = models.BooleanField(default=False)
    bookmarked = models.BooleanField(default=False)
    dead = models.BooleanField(blank=True, null=True)

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

    status_code = models.IntegerField(default=200)

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
        visits = EntryVisits.objects.filter(entry=self.link)

        sum_num = 0
        for visit in visits:
            sum_num += visit.visits

        return sum_num / visits.count()

    def update_calculated_vote(self):
        self.page_rating_votes = self.get_vote()
        self.page_rating_visits = self.get_visits()
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
        # TODO
        return []

    def update_language(self):
        if self.get_source_obj():
            self.language = self.get_source_obj().language
            self.save()
        else:
            from ..webtools import Page

            page = Page(self.link)
            if page.is_valid():
                language = page.get_language()
                if language != None:
                    self.language = language
                    self.save()

    def get_favicon(self):
        if self.get_source_obj():
            return self.get_source_obj().get_favicon()

        from ..webtools import Page

        page = Page(self.link)
        domain = page.get_domain()
        return domain + "/favicon.ico"

    def get_domain_only(self):
        from ..webtools import Page

        page = Page(self.link)
        return page.get_domain_only()

    def get_thumbnail(self):
        if self.age and self.age >= 18:
            return static("{0}/images/sign-304093_640.png".format(LinkDatabase.name))

        if self.thumbnail:
            return self.thumbnail

        return self.get_favicon()

    def get_export_names():
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
        names = BaseLinkDataController.get_export_names()
        names.append("source_obj__title")
        names.append("source_obj__category")
        names.append("source_obj__subcategory")
        names.append("tags__tag")
        names.append("votes__vote")
        return names

    def get_all_export_names():
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
            "tags",
            "comments",
            "vote",
        ]

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

        return themap

    def get_archive_link(self):
        from ..services.waybackmachine import WaybackMachine
        from ..dateutils import DateUtils

        m = WaybackMachine()
        formatted_date = m.get_formatted_date(self.date_published.date())
        archive_link = m.get_archive_url_for_date(formatted_date, self.link)
        return archive_link

    def get_full_information(data):
        return BaseLinkDataController.update_info(data)

    def update_info(data):
        from ..webtools import Page

        p = Page(data["link"])

        data["thumbnail"] = None

        if p.is_youtube():
            BaseLinkDataController.update_info_youtube(data)

        return BaseLinkDataController.update_info_default(data)

    def update_info_youtube(data):
        # TODO there should be some generic handlers
        from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

        h = YouTubeLinkHandler(data["link"])
        h.download_details()
        if h.get_video_code() is None:
            return data

        if "source" not in data or data["source"].strip() == "":
            data["source"] = h.get_channel_feed_url()
        data["link"] = h.get_link_url()
        if "title" not in data or data["title"].strip() == "":
            data["title"] = h.get_title()
        # TODO limit comes from LinkDataModel, do not hardcode
        if "description" not in data or data["description"].strip() == "":
            data["description"] = h.get_description()[:900]
        data["date_published"] = h.get_datetime_published()
        if (
            "thumbnail" not in data
            or data["thumbnail"] is None
            or data["thumbnail"].strip() == ""
        ):
            data["thumbnail"] = h.get_thumbnail()
        data["artist"] = h.get_channel_name()
        data["album"] = h.get_channel_name()

        return data

    def update_info_default(data):
        from ..webtools import Page

        p = Page(data["link"])
        if "source" not in data or not data["source"]:
            data["source"] = p.get_domain()
        if "artist" not in data or not data["artist"]:
            data["artist"] = p.get_domain()
        if "album" not in data or not data["album"]:
            data["album"] = p.get_domain()
        if "language" not in data or not data["language"]:
            data["language"] = p.get_language()
        if "title" not in data or not data["title"]:
            data["title"] = p.get_title()
        if "description" not in data or not data["description"]:
            data["description"] = p.get_title()

        sources = SourceDataModel.objects.filter(url=data["source"])
        if sources.count() > 0:
            data["artist"] = sources[0].title
            data["album"] = sources[0].title

        return data

    def make_bookmarked(self, username):
        self.bookmarked = True
        self.permanent = True
        self.user = username
        self.save()

    def make_not_bookmarked(self, username):
        from ..models import LinkTagsDataModel, LinkVoteDataModel

        self.permanent = False

        tags = LinkTagsDataModel.objects.filter(link_obj=self)
        tags.delete()

        votes = LinkVoteDataModel.objects.filter(link_obj=self)
        votes.delete()

        self.bookmarked = False
        self.user = username
        self.save()

    def is_taggable(self):
        return self.permanent or self.bookmarked

    def move_to_archive(self):
        objs = ArchiveLinkDataModel.objects.filter(link=self.link)
        if objs.count() == 0:
            themap = self.get_map()
            themap["source_obj"] = self.get_source_obj()
            try:
                ArchiveLinkDataModel.objects.create(**themap)
                self.delete()
            except Exception as e:
                error_text = traceback.format_exc()
        else:
            try:
                self.delete()
            except Exception as e:
                error_text = traceback.format_exc()

    def is_archive_entry(self):
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


class ArchiveLinkDataModel(BaseLinkDataController):
    source_obj = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="archive_source",
        null=True,
        blank=True,
    )

    def is_archive_entry(self):
        return True


class EntryVisits(models.Model):
    """
    Each user vists many places. This table keeps track of it
    """

    entry = models.CharField(max_length=1000)  # same as link
    user = models.CharField(max_length=1000, null=True, blank=True)
    visits = models.IntegerField(blank=True, null=True)

    entry_object = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="visits_counter",
    )

    def visited(entry, user):
        from ..configuration import Configuration
        from ..controllers import BackgroundJobController

        config = Configuration.get_object().config_entry

        if not config.track_user_actions:
            return

        if str(user) == "" or user is None:
            return

        visits = EntryVisits.objects.filter(entry=entry.link, user=user)

        if visits.count() == 0:
            visit = EntryVisits.objects.create(
                entry=entry.link, user=user, visits=1, entry_object=entry
            )
        else:
            visit = visits[0]
            visit.visits += 1
            visit.save()

        BackgroundJobController.update_entry_data(entry.link)

        return visit
