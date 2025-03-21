"""
API needs to check user privileges.

 - in order for any search engine to work all actions of user have to be captured
 - the causation needs to be established
 - the engine needs to know the person it tracks (does anonymization exist for search engines?)
"""

import time
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
import urllib.parse

from utils.dateutils import DateUtils

from .entries import LinkDataModel
from .system import AppLogging
from ..configuration import Configuration
from ..apps import LinkDatabase


class UserSearchHistory(models.Model):
    """
    Just a search history
    """

    search_query = models.CharField(max_length=1000)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_search_history",
        null=True,
    )

    class Meta:
        ordering = ["-date"]

    def add(user, search_query):
        if not user.is_authenticated:
            return

        config_entry = Configuration.get_object().config_entry
        if not config_entry.track_user_actions or not config_entry.track_user_searches:
            return

        if search_query is not None and search_query != "":
            if UserSearchHistory.get_top_query(user) == search_query:
                return

            UserSearchHistory.delete_old_user_entries(
                search_query=search_query, user=user
            )

            theobject = UserSearchHistory.objects.create(
                search_query=search_query, user=user
            )
            UserSearchHistory.delete_old_entries(user)

            return theobject

    def cleanup(cfg=None):
        config_entry = Configuration.get_object().config_entry
        if not config_entry.track_user_actions or not config_entry.track_user_searches:
            UserSearchHistory.objects.all().delete()

    def get_top_query(user):
        if not user.is_authenticated:
            return

        qs = UserSearchHistory.objects.filter(user=user).order_by("-date")
        if qs.exists():
            return qs[0]

    def get_user_choices(user):
        """
        We want ordered set, but I do not want to use any fancy type
        """
        choices = []

        if not user.is_authenticated:
            return choices

        qs = UserSearchHistory.objects.filter(user=user).order_by("-date")[
            : UserSearchHistory.get_choices_limit()
        ]

        return qs

    def delete_old_entries(user):
        qs = UserSearchHistory.objects.filter(user=user).order_by("date")

        row_limit = UserSearchHistory.get_choices_limit_memory()

        if row_limit == 0:  # no limit
            return

        if qs.count() > row_limit:
            too_many = qs.count() - row_limit
            entries = qs[:too_many]
            for entry in entries:
                entry.delete()

    def delete_old_user_entries(user, search_query):
        entries = UserSearchHistory.objects.filter(search_query=search_query, user=user)
        if entries.exists():
            entries.delete()

    def get_choices_limit():
        """
        Used for GUI
        """
        return 60

    def get_choices_limit_memory():
        """
        We may maintain more than we display in GUI
        """
        config_entry = Configuration.get_object().config_entry
        return config_entry.max_number_of_user_search

    def get_encoded_search_query(self):
        return urllib.parse.quote(self.search_query)


class UserEntryTransitionHistory(models.Model):
    """
    Keeps history of which link goes to where. From can be blank at start
    """

    counter = models.IntegerField(default=0)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_entry_transitions",
        null=True,
    )

    entry_from = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transitions_from",
    )
    entry_to = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transitions_to",
    )

    class Meta:
        ordering = ["-counter"]

    def get_related_list(user, navigated_to_entry):
        """ """
        result = []

        if not user.is_authenticated:
            return result

        config_entry = Configuration.get_object().config_entry
        max_related_links = config_entry.max_number_of_related_links

        link_transitions = UserEntryTransitionHistory.objects.filter(
            Q(user=user)
            & (Q(entry_from=navigated_to_entry) | Q(entry_to=navigated_to_entry))
        ).order_by("-counter")

        if link_transitions.exists():
            index = 0
            for link_info in link_transitions:
                entries = None

                if navigated_to_entry == link_info.entry_to:
                    if link_info.entry_from:
                        entries = LinkDataModel.objects.filter(
                            id=link_info.entry_from.id
                        )
                else:
                    if link_info.entry_to:
                        entries = LinkDataModel.objects.filter(id=link_info.entry_to.id)

                if entries and entries.exists():
                    entry = entries[0]
                    if entry not in result:
                        result.append(entry)
                index += 1

                if index > max_related_links:
                    break

        return result

    def add(user, entry_from, entry_to):
        config_entry = Configuration.get_object().config_entry
        if (
            not config_entry.track_user_actions
            or not config_entry.track_user_navigation
        ):
            return

        if entry_from == entry_to:
            return

        element = UserEntryTransitionHistory.get_element(user, entry_from, entry_to)

        if element:
            element.counter += 1
            element.save()
            return element

        else:
            return UserEntryTransitionHistory.objects.create(
                entry_from=entry_from, entry_to=entry_to, counter=1, user=user
            )

    def get_element(user, entry_from, entry_to):
        links = UserEntryTransitionHistory.objects.filter(
            user=user, entry_from=entry_from, entry_to=entry_to
        ).order_by("-counter")
        if links.exists():
            return links[0]

    def cleanup(cfg=None):
        if cfg and "verify" in cfg:
            for transition in UserEntryTransitionHistory.objects.all():
                try:
                    id = transition.entry_from.id
                except Exception as E:
                    transition.delete()
                try:
                    id = transition.entry_to.id
                except Exception as E:
                    transition.delete()

        config_entry = Configuration.get_object().config_entry
        if (
            not config_entry.track_user_actions
            or not config_entry.track_user_navigation
        ):
            UserEntryTransitionHistory.objects.all().delete()

    def move_entry(source_entry, destination_entry):
        """
        We move entry from https:// to http://. We want that history to be preserved
        """
        transitions = UserEntryTransitionHistory.objects.filter(entry_from=source_entry)
        for transition in transitions:
            dst_transitions = UserEntryTransitionHistory.objects.filter(
                entry_from=destination_entry, user=transition.user
            )
            if dst_transitions.exists():
                dst_transition = dst_transitions[0]
                dst_transition.counter += transition.counter
                dst_transition.save()

                transition.delete()
                continue

            transition.entry_from = destination_entry
            transition.save()

        transitions = UserEntryTransitionHistory.objects.filter(entry_to=source_entry)
        for transition in transitions:
            dst_transitions = UserEntryTransitionHistory.objects.filter(
                entry_to=destination_entry, user=transition.user
            )
            if dst_transitions.exists():
                dst_transition = dst_transitions[0]
                dst_transition.counter += transition.counter
                dst_transition.save()

                transition.delete()
                continue

            transition.entry_from = destination_entry
            transition.save()


class UserEntryVisitHistory(models.Model):
    """
    Keeps info how many times user entered link,
    TODO maybe rename to userentrynavigation?
    """

    visits = models.IntegerField(blank=True, null=True)
    date_last_visit = models.DateTimeField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_entry_visits",
        null=True,
    )

    entry = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="visits_counter",
    )

    class Meta:
        ordering = ["-date_last_visit"]

    def visited(entry, user, previous_entry=None):
        """
        User visited a link:
         - if it is just hit before a minute (f5 etc.) do nothing
         - if we transitioned from other link store that info
         - increment visits counter
        """
        from ..configuration import Configuration
        from ..controllers import BackgroundJobController

        """
        TODO to think about. are we capturing data about not logged users?
        """
        if not user.is_authenticated:
            print("user is not authenticated")
            return

        config = Configuration.get_object().config_entry

        # ignore misinformation, etc.
        if entry.get_vote() < 0:
            return

        if not config.track_user_actions or not config.track_user_navigation:
            return

        if str(user.username) == "" or user.username is None:
            return

        if UserEntryVisitHistory.is_link_just_visited(user, entry):
            return

        if not previous_entry:
            previous_entry = UserEntryVisitHistory.get_last_user_entry(user)

        visits = UserEntryVisitHistory.objects.filter(user=user, entry=entry)

        if visits.count() == 0:
            visit = UserEntryVisitHistory.objects.create(
                visits=1,
                entry=entry,
                date_last_visit=DateUtils.get_datetime_now_utc(),
                user=user,
            )
        else:
            visit = visits[0]
            visit.visits += 1
            visit.date_last_visit = DateUtils.get_datetime_now_utc()
            visit.user = user
            visit.save()

        if previous_entry:
            UserEntryTransitionHistory.add(user, previous_entry, entry)

        UserEntryVisitHistory.delete_old_entries(user)

        # to increment visited counter on entry
        # BackgroundJobController.entry_update_data(entry)
        # TODO - there should be recalculated JOB. we do not want to udpate it's data

        return visit

    def is_link_just_visited(user, entry):
        last_entry = UserEntryVisitHistory.get_last_user_entry(user)
        if last_entry != entry:
            return False

        visits = UserEntryVisitHistory.objects.filter(user=user, entry=entry)

        if (
            visits.count() > 0
            and visits[0].date_last_visit
            and visits[0].date_last_visit
            > DateUtils.get_datetime_now_utc() - timedelta(minutes=1)
        ):
            return True

        return False

    def is_visited(user, entry):
        """
        Used to determine entry visibility in lists.
        If user is not authenticated, all entries should be visible, therefore state 'True'
        The flag only makes sense if user actions are tracked, and user is authenticated.
        """
        if not user.is_authenticated:
            return True

        config_entry = Configuration.get_object().config_entry
        if (
            not config_entry.track_user_actions
            or not config_entry.track_user_navigation
        ):
            return True

        histories = UserEntryVisitHistory.objects.filter(
            user=user,
            entry=entry,
        )

        if histories.count() > 0:
            history = histories[0]
            if entry.visits > 0:
                return True

        return False

    def get_last_user_entry(user):
        """
        Check last browsed entry.
         - entries older than 1 hour do not count (user has stopped 'watching')
         - user may open 10 tabs immediately. Therefore we use smaller limit also
         - if user opens 10 tabs after 1 hour stop, we return the oldest one
        """
        if not user.is_authenticated:
            return

        time_ago_limit = DateUtils.get_datetime_now_utc() - timedelta(hours=1)
        burst_time_limit = DateUtils.get_datetime_now_utc() - timedelta(seconds=15)

        entries = UserEntryVisitHistory.objects.filter(
            user=user,
            date_last_visit__gt=time_ago_limit,
            date_last_visit__lt=burst_time_limit,
        ).order_by("-date_last_visit")
        if entries.exists():
            return entries[0].entry

        # something might be in burst time

        entries = UserEntryVisitHistory.objects.filter(
            user=user,
            date_last_visit__gt=time_ago_limit,
        ).order_by("date_last_visit")
        if entries.exists():
            return entries[0].entry

    def cleanup(cfg=None):
        if cfg and "verify" in cfg:
            for visit in UserEntryVisitHistory.objects.all():
                try:
                    id = visit.entry.id
                except Exception as E:
                    visit.delete()
                try:
                    id = visit.user.id
                except Exception as E:
                    visit.delete()

        config_entry = Configuration.get_object().config_entry
        if (
            not config_entry.track_user_actions
            or not config_entry.track_user_navigation
        ):
            UserEntryVisitHistory.objects.all().delete()

    def move_entry(source_entry, destination_entry):
        visits = UserEntryVisitHistory.objects.filter(entry=source_entry)
        for visit in visits:
            dst_visits = UserEntryVisitHistory.objects.filter(
                entry=destination_entry, user=visit.user
            )
            if dst_visits.exists():
                dst_visit = dst_visits[0]
                dst_visit.visits += visit.visits
                if visit.date_last_visit > dst_visit.date_last_visit:
                    dst_visit.date_last_visit = visit.date_last_visit
                dst_visit.save()

                visit.delete()
                continue

            visit.entry = destination_entry
            visit.save()

    def delete_old_entries(user):
        qs = UserEntryVisitHistory.objects.filter(user=user).order_by("date_last_visit")

        config_entry = Configuration.get_object().config_entry
        if config_entry.max_user_entry_visit_history == 0:
            return

        limit = config_entry.max_user_entry_visit_history
        if qs.count() > limit:
            too_many = qs.count() - limit
            entries = qs[:too_many]
            for entry in entries:
                entry.delete()


class EntryHitUserSearchHistory(models.Model):
    """
    User searches for something. Then clicks a link. That is a hit.
    Store it here. Match between search & hit.

    TODO
    """

    search_query = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000, unique=True)
    user = models.CharField(max_length=1000)

    def add(user, search_query, link):
        UserSearchHistory.objects.create(
            search_query=search_query, user=user, link=link
        )


class EntryHitSearchHistory(models.Model):
    """
    Same as previous, but for all users.
    TODO How to rank it?

    TODO
    """

    search_query = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000, unique=True)
    vote = models.IntegerField(default=0)
