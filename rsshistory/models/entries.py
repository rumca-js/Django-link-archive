from datetime import datetime, date, timedelta

from django.db import models
from django.urls import reverse

from ..apps import LinkDatabase
from .sources import SourceDataModel
from .admin import PersistentInfo


class BaseLinkDataModel(models.Model):
    source = models.CharField(max_length=2000)
    title = models.CharField(max_length=1000, null=True)
    description = models.TextField(max_length=1000, null=True)
    link = models.CharField(max_length=1000, unique=True)
    date_published = models.DateTimeField(default=datetime.now)
    # this entry cannot be removed
    bookmarked = models.BooleanField(default=False)
    # this entry is dead indication
    dead = models.BooleanField(default=False)
    artist = models.CharField(max_length=1000, null=True, default=None)
    album = models.CharField(max_length=1000, null=True, default=None)
    # user who added entry
    user = models.CharField(max_length=1000, null=True, default=None)

    # possible values en-US, or pl_PL
    language = models.CharField(max_length=10, null=True, default=None)
    thumbnail = models.CharField(max_length=1000, null=True, default=None)

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
        string = "{} {}".format(self.date_published, self.get_source_name())
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
        try:
            if not getattr(self, "votes"):
                return 0
        except Exception as E:
            return 0

        votes = self.votes.all()
        if votes.count() == 0:
            return 0

        sum_num = None
        for vote in votes:
            if sum_num == None:
                sum_num = vote.vote
            else:
                sum_num += vote.vote

        return sum_num / len(votes)

    def get_tag_map(self):
        # TODO should it be done by for tag in self.tags: tag.get_map()?
        result = []
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
            "bookmarked",
            "dead",
            "artist",
            "album",
            "user",
            "language",
            "thumbnail",
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
            "bookmarked",
            "dead",
            "artist",
            "album",
            "user",
            "language",
            "thumbnail",
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

        vote = self.get_vote()
        if vote > 0:
            themap["vote"] = tags

        comments = self.get_comment_vec()
        if len(comments) > 0:
            themap["comments"] = comments

        return themap

    def get_archive_link(self):
        from ..services.waybackmachine import WaybackMachine
        from ..dateutils import DateUtils

        m = WaybackMachine()
        formatted_date = m.get_formatted_date(self.date_published.date())
        archive_link = m.get_archive_url_for_date(formatted_date, self.link)
        return archive_link

    def create_from_youtube(url, data):
        from ..pluginentries.youtubelinkhandler import YouTubeLinkHandler

        objs = BaseLinkDataModel.objects.filter(link=url)
        if objs.count() != 0:
            return False

        h = YouTubeLinkHandler(url)
        if not h.download_details():
            PersistentInfo.error("Could not obtain details for link:{}".format(url))
            return False

        data = dict()
        source = h.get_channel_feed_url()
        if source is None:
            PersistentInfo.error("Could not obtain channel feed url:{}".format(url))
            return False

        link = h.get_link_url()
        title = h.get_title()
        description = h.get_description()
        date_published = h.get_datetime_published()
        thumbnail = h.get_thumbnail()
        artist = h.get_channel_name()

        language = "en-US"
        if "language" in data:
            language = data["language"]
        user = None
        if "user" in data:
            user = data["user"]
        bookmarked = False
        if "bookmarked" in data:
            bookmarked = data["bookmarked"]

        source_obj = None
        sources = SourceDataModel.objects.filter(url=source)
        if sources.exists():
            source_obj = sources[0]

        entry = LinkDataModel(
            source=source,
            title=title,
            description=description,
            link=link,
            date_published=date_published,
            bookmarked=bookmarked,
            thumbnail=thumbnail,
            artist=artist,
            language=language,
            user=user,
            source_obj=source_obj,
        )
        entry.save()
        return True

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
        self.user = username
        self.save()

    def make_not_bookmarked(self, username):
        from ..models import LinkTagsDataModel, LinkVoteDataModel

        tags = LinkTagsDataModel.objects.filter(link_obj=self)
        tags.delete()

        votes = LinkVoteDataModel.objects.filter(link_obj=self)
        votes.delete()

        self.bookmarked = False
        self.user = username
        self.save()

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

    def get_archive_days_limit():
        return 100

    def is_archive_entry(self):
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
