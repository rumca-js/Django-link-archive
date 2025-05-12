from django.db import models
from django.conf import settings
from django.db.models import Q
from django.templatetags.static import static

from datetime import datetime, timedelta

from ..apps import LinkDatabase
from .entries import LinkDataModel


class SearchView(models.Model):
    """
    Search view, in which user can browse entries according to liking.
    Admins can provide more views.
    """

    name = models.CharField(
        blank=True,
        max_length=500,
        help_text="Name",
    )

    default = models.BooleanField(
        default=False, help_text="If true, then this is default view."
    )

    hover_text = models.CharField(
        blank=True,
        max_length=500,
        help_text="Text displayed on button hover",
    )

    filter_statement = models.CharField(
        blank=True,
        max_length=500,
        help_text="Filter, if any. Maybe you are interested only in bookmarked entries?",
    )

    icon = models.CharField(
        default=static("{}/icons/icons8-search-100.png".format(LinkDatabase.name)),
        max_length=500,
        help_text="Icon",
    )

    order_by = models.CharField(
        default="link",
        max_length=500,
        help_text="Entries order",
    )

    entry_limit = models.IntegerField(
        default=0,
        help_text="0 means no limit.",
    )

    auto_fetch = models.BooleanField(
        default=False, help_text="When view is access it immediately fetches data."
    )

    date_published_day_limit = models.IntegerField(
        default=0, help_text="The number of days limit."
    )

    date_created_day_limit = models.IntegerField(
        default=0, help_text="The number of days limit."
    )

    user = models.BooleanField(
        default=False,
        help_text="If true, then it is 'user' view. Otherwise it is generic view.",
    )

    class Meta:
        ordering = ["-default", "id"]

    def get_conditions(self):
        from ..queryfilters import DjangoEquationProcessor

        if self.filter_statement != "":
            processor = DjangoEquationProcessor(self.filter_statement)
            conditions = processor.get_conditions()
        else:
            conditions = Q()

        if self.date_published_day_limit != 0:
            date_published_date = datetime.now() - timedelta(
                days=self.date_published_day_limit
            )

            conditions &= Q(date_published__gt=date_published_date)

        if self.date_created_day_limit != 0:
            date_created_date = datetime.now() - timedelta(
                days=self.date_created_day_limit
            )
            conditions &= Q(date_created__gt=date_created_date)

        return conditions

    def get_conditions_str(self):
        from ..queryfilters import DjangoEquationProcessor

        if self.filter_statement != "":
            processor = DjangoEquationProcessor(self.filter_statement)
            conditions = processor.get_conditions()
        else:
            conditions = Q()

        if self.date_published_day_limit != 0:
            date_published_date = datetime.now() - timedelta(
                days=self.date_published_day_limit
            )

            conditions &= Q(date_published__gt=date_published_date)

        if self.date_created_day_limit != 0:
            date_created_date = datetime.now() - timedelta(
                days=self.date_created_day_limit
            )
            conditions &= Q(date_created__gt=date_created_date)

        return conditions

    def reset():
        views = SearchView.objects.all()
        views.delete()

        SearchView.objects.create(
            name="Default",
            order_by="-page_rating_votes, -page_rating, link",
            default=True,
            hover_text="Search",
        )
        SearchView.objects.create(
            name="Bookmarked",
            filter_statement="bookmarked=True",
            order_by="-date_created, link",
            user=True,
            hover_text="Search bookmars",
        )
        SearchView.objects.create(
            name="Search by votes",
            order_by="-page_rating_votes, -page_rating, link",
            entry_limit=1000,
            hover_text="Searches by rating votes",
        )
        SearchView.objects.create(
            name="What's created",
            order_by="-date_created, link",
            date_published_day_limit=7,
            hover_text="Search by date created",
        )
        SearchView.objects.create(
            name="What's published",
            order_by="-date_published, link",
            date_published_day_limit=7,
            hover_text="Search by date published",
        )
        SearchView.objects.create(
            name="Search all",
            order_by="-date_created, link",
            hover_text="Searches all entries",
        )
