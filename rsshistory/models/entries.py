from datetime import date, timedelta
import traceback

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.templatetags.static import static
from django.utils import timezone
from django.conf import settings

from ..webtools import UrlLocation
from utils.dateutils import DateUtils
from utils.controllers import GenericEntryController

from ..apps import LinkDatabase

from .sources import SourceDataModel
from .system import AppLogging
from .domains import Domains


class BaseLinkDataModel(models.Model):
    STATUS_UNDEFINED = 0
    STATUS_DEAD = 500
    STATUS_ACTIVE = 200

    MANUAL_STATUS_CODES = (
        (STATUS_UNDEFINED, "UNDEFINED"),
        (STATUS_DEAD, "DEAD"),
        (STATUS_ACTIVE, "ACTIVE"),
    )

    link = models.CharField(max_length=1000, unique=True)

    # URL of source, might be RSS source
    source_url = models.CharField(blank=True, max_length=2000)

    title = models.CharField(max_length=1000, null=True, blank=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    thumbnail = models.CharField(max_length=1000, null=True, blank=True)
    language = models.CharField(max_length=10, null=True, blank=True)
    age = models.IntegerField(
        blank=True, null=True, help_text="Age limit to view entry"
    )

    # DB - date when entry was created
    date_created = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Date when entry was created in the database",
    )

    # web page publication date
    date_published = models.DateTimeField(
        help_text="Date when page was published",
        null=True,
    )

    # web page date when link was found dead. Manual can change 'visible' state of entry
    # but does not affect this flag.
    date_dead_since = models.DateTimeField(
        null=True, help_text="Date when page became inactive"
    )

    # DB - date when entry was accessed last by scanned
    date_update_last = models.DateTimeField(
        null=True, help_text="Date when page was last checked"
    )

    # web page date of last modification
    date_last_modified = models.DateTimeField(
        null=True, help_text="Date of last page modification"
    )

    # this entry cannot be removed. Serves a purpose. Domain page, source page
    permanent = models.BooleanField(
        default=False,
        help_text="Flag automatically used by the system preventing removing of entries",
    )
    bookmarked = models.BooleanField(
        default=False, help_text="This entry will not be automatically removed"
    )

    # We could use a different model, but it may lead to making multiple queries
    # For each model.

    # Archive was introduced to have two tables:
    #  - link model (fast)
    #  - archive (slow)

    # If we have moved author & album to one big table, then it would go against this
    # solution.
    # We do not want to have archive tables for everything.

    author = models.CharField(max_length=1000, null=True, blank=True)
    album = models.CharField(max_length=1000, null=True, blank=True)

    status_code = models.IntegerField(default=0)
    manual_status_code = models.IntegerField(default=0, null=True, blank=True)
    contents_type = models.IntegerField(default=0)  # indicates if it is rss, html, etc.

    page_rating_contents = models.IntegerField(default=0)
    page_rating_votes = models.IntegerField(default=0)
    page_rating_visits = models.IntegerField(default=0)
    page_rating = models.IntegerField(default=0)

    contents_hash = models.BinaryField(max_length=30, null=True)
    body_hash = models.BinaryField(max_length=30, null=True)

    class Meta:
        abstract = True
        ordering = ["-date_published", "source_url", "title"]

        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["link"]),
            models.Index(fields=["date_published"]),
        ]

    def save(self, *args, **kwargs):
        """
        We can fix some database errors here.
        We can trim title and description. No harm done.
        We cannot trim thumbnails, or link, it will not work after adding.
        """
        link_length = BaseLinkDataModel._meta.get_field("link").max_length
        title_length = BaseLinkDataModel._meta.get_field("title").max_length
        description_length = BaseLinkDataModel._meta.get_field("description").max_length
        author_length = BaseLinkDataModel._meta.get_field("author").max_length
        album_length = BaseLinkDataModel._meta.get_field("album").max_length
        thumbnail_length = BaseLinkDataModel._meta.get_field("thumbnail").max_length
        language_length = BaseLinkDataModel._meta.get_field("language").max_length

        if len(self.link) >= link_length:
            AppLogging.error(
                "URL:{} URL is too long, cannot save such link".format(self.link)
            )
            return

        # Trim the input string to fit within max_length
        if self.title and len(self.title) > title_length:
            AppLogging.error("URL:{} Title length is too long".format(self.link))
            self.title = self.title[: title_length - 1]

        if self.description and len(self.description) > description_length:
            AppLogging.error("URL:{} Description length is too long".format(self.link))
            self.description = self.description[: description_length - 1]

        if self.thumbnail and len(self.thumbnail) > thumbnail_length:
            AppLogging.error("URL:{} Thumbnail length is too long".format(self.link))
            self.thumbnail = None

        if self.language and len(self.language) > language_length:
            AppLogging.error(
                "URL:{} Incorrect language:{}".format(self.link, self.language)
            )
            self.language = None

        if self.album and len(self.album) > album_length:
            AppLogging.error("URL:{} Album length is too long".format(self.link))
            self.album = self.description[: album_length - 1]

        if self.author and len(self.author) > author_length:
            AppLogging.error("URL:{} Author length is too long".format(self.link))
            self.author = self.description[: author_length - 1]

        p = UrlLocation(self.link)
        if p.is_domain():
            domain = self.get_domain_safe()

            if domain:
                domain.update(self)

        self.permanent = self.should_entry_be_permanent()

        super().save(*args, **kwargs)

    def get_domain_safe(self):
        try:
            if hasattr(self, "domain"):
                if self.domain != None:
                    return self.domain
        except Exception as E:
            self.domain = None
            AppLogging.debug(str(E))

    def get_field_length(field):
        length = BaseLinkDataModel._meta.get_field(field).max_length
        return length

    def delete(self, *args, **kwargs):
        p = UrlLocation(self.link)
        if p.is_domain():
            domains = Domains.objects.filter(domain=p.get_domain_only())
            domains.delete()

        super().delete(*args, **kwargs)


class BaseLinkDataController(BaseLinkDataModel):
    class Meta:
        abstract = True
        ordering = ["-date_published", "source_url", "title"]

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

    def get_protocol_img(self):
        if self.link.startswith("ftp://"):
            return static("{0}/icons/icons8-ftp-96.png".format(LinkDatabase.name))
        elif self.link.startswith("smb://"):
            return static("{0}/icons/icons8-nas-96.png".format(LinkDatabase.name))
        elif self.link.startswith("http://"):
            return static("{0}/icons/icons8-unlocked-96.png".format(LinkDatabase.name))
        elif self.link.startswith("https://"):
            return static("{0}/icons/icons8-locked-100.png".format(LinkDatabase.name))

    def get_source_name(self):
        if self.source:
            return self.source.title
        else:
            return self.source_url

    def get_link_dead_text(self):
        return "______"

    def get_title_safe(self):
        c = GenericEntryController(self)
        return c.get_title()

    def get_long_description(self):
        if self.is_dead():
            return self.get_link_dead_text()
        return "{} {}".format(self.date_published, self.get_source_name())

    def has_tags(self):
        if not hasattr(self, "tags"):
            return 0

        return len(self.tags.all()) > 0

    def get_full_description(self):
        if self.is_dead():
            return self.get_link_dead_text()
        string = self.get_long_description()

        tags = self.get_tag_string()
        if tags:
            string += " Tags:{}".format(tags)
        if self.user:
            string += " User:{}".format(self.user_object.username)

        return string

    def get_local_date_published(self):
        from ..configuration import Configuration

        c = Configuration.get_object()
        return c.get_local_time(self.date_published)

    def get_tag_string(self):
        from .models import LinkTagsDataModel

        return LinkTagsDataModel.join_elements(self.tags.all())

    def get_vote(self):
        return self.page_rating_votes

    def get_tag_map(self):
        # TODO should it be done by for tag in self.tags: tag.get_map()?
        result = []

        tags = self.tags.all().order_by("tag")
        for tag in tags:
            result.append(tag.tag)
        return result

    def get_comment_vec(self):
        result = []

        comments = self.comments.all()
        for comment in comments:
            data = {}
            data["comment"] = comment.comment
            data["user_name"] = comment.user.username
            data["user_id"] = comment.user.id
            data["entry_id"] = comment.entry.id
            data["date_published"] = comment.date_published.isoformat()
            data["date_edited"] = comment.date_published.isoformat()
            data["reply_id"] = comment.reply_id
            result.append(data)

        return result

    def update_language(self):
        if self.source:
            self.language = self.source.language
            self.save()
        else:
            from ..pluginurl import UrlHandlerEx

            handler = UrlHandlerEx(self.link)
            if handler.is_valid():
                language = handler.get_language()
                if language != None:
                    self.language = language
                    self.save()

    def get_favicon(self):
        """
        Prints favicon from source, or from HTML page directly
        """
        if self.age and self.age >= 18:
            return static("{0}/images/sign-304093_640.png".format(LinkDatabase.name))

        if self.source:
            return self.source.get_favicon()

        # returning real favicon from HTML is too long
        return UrlLocation(self.link).get_domain() + "/favicon.ico"

    def get_domain_only(self):
        page = UrlLocation(self.link)
        return page.get_domain_only()

    def get_thumbnail(self):
        """
        Prints thumbnail, but if it does not have one prints favicon
        """
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry

        thumbnail_url = self.get_thumbnail_url()

        if conf.enable_file_support:
            from .modelfiles import ModelFiles

            if thumbnail_url:
                model_files = ModelFiles.objects.filter(file_name=thumbnail_url)
                if model_files.exists():
                    return model_files[0].get_url()

        return thumbnail_url

    def get_thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail

        return self.get_favicon()

    def get_export_names():
        """
        Provides object export names. No dependencies towards other objects
        """
        return [
            "id",
            "source_url",
            "title",
            "description",
            "link",
            "date_created",
            "date_published",
            "date_dead_since",
            "permanent",
            "bookmarked",
            "author",
            "album",
            "language",
            "thumbnail",
            "age",
            "page_rating_contents",
            "page_rating_votes",
            "page_rating_visits",
            "page_rating",
            "manual_status_code",
            "status_code",
        ]

    def get_query_names():
        names = set(BaseLinkDataController.get_export_names())
        names.add("source__id")
        names.add("source__url")
        names.add("source__title")
        names.add("source__category_name")
        names.add("source__subcategory_name")
        names.add("source__category_id")
        names.add("source__subcategory_id")

        names.add("tags__id")
        names.add("tags__tag")
        names.add("compacted_tags__id")
        names.add("compacted_tags__tag")
        names.add("votes__id")
        names.add("votes__vote")

        names.add("user__id")
        names.add("user__username")

        names.add("date_created")
        names.add("date_dead_since")
        names.add("date_update_last")
        return sorted(list(names))

    def get_all_export_names():
        """
        Provides object export names with dependencies from other objects
        """
        names = set(BaseLinkDataController.get_export_names())
        names.add("source__id")
        names.add("user__id")
        names.add("tags")
        names.add("comments")
        names.add("vote")  # TODO is this used?
        return list(names)

    def get_map(self, stringify=True):
        output_data = {}

        export_names = BaseLinkDataController.get_export_names()
        for export_name in export_names:
            val = getattr(self, export_name)

            if stringify:
                if export_name.find("date_") >= 0:
                    if val:
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

        if self.source:
            themap["source__id"] = self.source.id

        return themap

    def get_archive_link(self):
        from ..services.waybackmachine import WaybackMachine

        m = WaybackMachine()
        formatted_date = m.get_formatted_date(self.date_published.date())
        archive_link = m.get_archive_url_for_date(formatted_date, self.link)
        return archive_link

    def make_bookmarked(self):
        self.bookmarked = True
        self.save()

    def make_not_bookmarked(self):
        self.bookmarked = False
        self.save()

    def make_manual_dead(self):
        """
        Should we remove all tags & comments?
        """

        self.manual_status_code = BaseLinkDataController.STATUS_DEAD

        if not self.is_valid() and self.date_dead_since is None:
            self.date_dead_since = DateUtils.get_datetime_now_utc()

        self.save()

    def make_manual_active(self):
        self.manual_status_code = BaseLinkDataController.STATUS_ACTIVE

        if self.date_dead_since:
            self.date_dead_since = None

        self.save()

    def clear_manual_status(self):
        self.manual_status_code = BaseLinkDataController.STATUS_UNDEFINED

        if self.is_valid():
            self.date_dead_since = None
        if not self.is_valid() and self.date_dead_since is None:
            self.date_dead_since = DateUtils.get_datetime_now_utc()

        self.save()

    def is_taggable(self):
        """
        We do not want to check any state of entry.
        Users may want to tag dead entries, or malicious sites
        """
        if self.is_archive_entry():
            return False

        # return self.permanent or self.bookmarked
        return True

    def is_commentable(self):
        if self.is_archive_entry():
            return False

        # return self.permanent or self.bookmarked
        return True

    def is_permanent(self):
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry

        return self.permanent or self.bookmarked

    def is_removable(self):
        if self.permanent or self.bookmarked:
            return False

        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry
        if self.page_rating_votes > conf.remove_entry_vote_threshold:
            return False

        return True

    def get_days_dead(self):
        if not self.date_dead_since:
            return 0

        current_time = DateUtils.get_datetime_now_utc()

        delta = current_time - self.date_dead_since
        return delta.days

    def should_entry_be_permanent(self):
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry

        p = UrlLocation(self.link)

        # this entry represents source
        if self.source:
            if self.link == self.source.url:
                return self.source.enabled

        return False

    def is_dead(self):
        """
        We do not have to make elaborate checks for statuses and manual statuses.
        If there is a dead date -> it is dead. Period.
        """
        if self.manual_status_code == BaseLinkDataController.STATUS_ACTIVE:
            return False
        if self.manual_status_code == BaseLinkDataController.STATUS_DEAD:
            return True

        if self.date_dead_since is not None:
            return True

        """
        Link is not valid:
         - if status indicates so
         - if it is dead (manual indication)
         - if it was downvoted to oblivion
        """
        if self.manual_status_code == BaseLinkDataController.STATUS_UNDEFINED:
            return not self.is_status_code_valid() and self.page_rating == 0

        return False

    def is_https(self):
        return self.link.lower().startswith("https://")

    def is_http(self):
        return self.link.lower().startswith("http://")

    def get_http_url(self):
        p = UrlLocation(self.link)
        return p.get_protocol_url("http")

    def get_https_url(self):
        p = UrlLocation(self.link)
        return p.get_protocol_url("https")

    def is_valid(self):
        """ """
        if self.is_dead():
            return False

        return True

    def is_status_code_valid(self):
        from ..pluginurl import UrlHandlerEx

        handler = UrlHandlerEx(self.link)

        if handler.is_status_code_invalid(self.status_code):
            return False

        return True

    def is_archive_entry(self):
        """
        TODO: change to is_archive()
        """
        return False

    def is_archive_by_date(input_date):
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry
        if conf.days_to_move_to_archive == 0:
            return False

        date_to_move = DateUtils.get_days_before_dt(conf.days_to_move_to_archive)

        if input_date < date_to_move:
            return True
        return False

    def is_removed_by_date(input_date):
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry
        if conf.days_to_remove_links == 0:
            return False

        date_to_remove = DateUtils.get_days_before_dt(conf.days_to_remove_links)

        if input_date < date_to_remove:
            return True
        return False

    def get_description_safe(self):
        if not self.description or self.description == "":
            return ""

        length = BaseLinkDataController.get_description_length()

        return self.description[: length - 1]

    def get_description_for_add(description):
        """
        Forms can add \r, we need to compensate for that
        """
        if not description or description == "":
            return description

        if description.find("\r") > 0:
            return description

        length = BaseLinkDataController.get_description_length()

        description = description[: length - 1]
        lines_number = description.count("\n")
        description = description[:-lines_number]
        return description

    def get_description_length():
        return BaseLinkDataController._meta.get_field("description").max_length

    def is_user_appropriate(self, user):
        from .system import UserConfig

        if self.age and self.age != 0:
            if not user.is_authenticated:
                return False

            uc = UserConfig.get(user)
            age = uc.get_age()
            return self.age < age

        return True

    def is_update_time(self):
        if self.date_update_last is None:
            return True

        return self.date_update_last < DateUtils.get_datetime_now_utc() - timedelta(
            days=30
        )

    def is_reset_time(self):
        if self.date_update_last is None:
            return True

        return self.date_update_last < DateUtils.get_datetime_now_utc() - timedelta(
            days=1
        )


class LinkDataModel(BaseLinkDataController):
    source = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="link_source",
        null=True,
        blank=True,
    )
    domain = models.ForeignKey(
        Domains,
        on_delete=models.SET_NULL,
        related_name="entry_objects",
        null=True,
        blank=True,
    )
    # user who added entry
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_entries",
        null=True,
        blank=True,
    )

    def cleanup_http_duplicate(self):
        """
        If this is http entry, and we have https entry -> remove this
        """
        url = self.link
        if url.startswith("http:"):
            new_url = url.replace("http://", "https://")
            entries = LinkDataModel.objects.filter(link=new_url)
            if entries.count() > 0:
                self.delete()


class ArchiveLinkDataModel(BaseLinkDataController):
    source = models.ForeignKey(
        SourceDataModel,
        on_delete=models.SET_NULL,
        related_name="archive_source",
        null=True,
        blank=True,
    )
    domain = models.ForeignKey(
        Domains,
        on_delete=models.CASCADE,
        related_name="archive_entry_objects",
        null=True,
        blank=True,
    )
    # user who added entry
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_aentries",
        null=True,
    )

    def is_archive_entry(self):
        return True

    def cleanup_http_duplicate(self):
        """
        If this is http entry, and we have https entry -> remove this
        """
        url = self.link
        if url.startswith("http:"):
            new_url = url.replace("http://", "https://")
            entries = ArchiveLinkDataModel.objects.filter(link=new_url)
            if entries.count() > 0:
                self.delete()
