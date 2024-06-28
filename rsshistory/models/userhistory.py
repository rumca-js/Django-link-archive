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

from .entries import LinkDataModel
from ..configuration import Configuration
from ..apps import LinkDatabase

from .system import AppLogging


class UserSearchHistory(models.Model):
    """
    Just a search history
    """

    search_query = models.CharField(max_length=1000)
    date = models.DateTimeField(auto_now_add=True)
    user_object = models.ForeignKey(
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

            try:
                UserSearchHistory.delete_old_user_entries(
                    search_query=search_query, user=user
                )

                theobject = UserSearchHistory.objects.create(
                    search_query=search_query, user_object=user
                )
                UserSearchHistory.delete_old_entries(user)

                return theobject
            except Exception as E:
                LinkDatabase.info(str(E))

    def cleanup():
        config_entry = Configuration.get_object().config_entry
        if not config_entry.track_user_actions or not config_entry.track_user_searches:
            UserSearchHistory.objects.all().delete()

        # safety cleanup, if user is not set
        qs = UserSearchHistory.objects.filter(user_object__isnull=True)
        for q in qs:
            users = User.objects.filter(username=q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.info("Removing invalid search")
                q.delete()
                time.sleep(0.5)

    def get_top_query(user):
        if not user.is_authenticated:
            return

        qs = UserSearchHistory.objects.filter(user_object=user).order_by("-date")
        if qs.exists():
            return qs[0]

    def get_user_choices(user):
        """
        We want ordered set, but I do not want to use any fancy type
        """
        choices = []

        if not user.is_authenticated:
            return choices

        qs = UserSearchHistory.objects.filter(user_object=user).order_by("-date")[
            : UserSearchHistory.get_choices_limit()
        ]

        for q in qs:
            if q.search_query not in choices:
                choices.append(q.search_query)

        return choices

    def delete_old_entries(user):
        qs = UserSearchHistory.objects.filter(user_object=user).order_by("date")
        limit = UserSearchHistory.get_choices_model_limit()
        if qs.count() > limit:
            too_many = qs.count() - limit
            entries = qs[:too_many]
            for entry in entries:
                entry.delete()

    def delete_old_user_entries(user, search_query):
        entries = UserSearchHistory.objects.filter(
            search_query=search_query, user_object=user
        )
        if entries.exists():
            entries.delete()

    def get_choices_model_limit():
        """
        TODO move this to configuration?
        """
        return 300

    def get_choices_limit():
        return 60


class UserEntryTransitionHistory(models.Model):
    """
    Keeps history of which link goes to where. From can be blank at start
    """

    counter = models.IntegerField(default=0)
    user_object = models.ForeignKey(
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
        """
        order by counte
        """
        result = []

        if not user.is_authenticated:
            return result

        links = UserEntryTransitionHistory.objects.filter(
            user_object=user, entry_from=navigated_to_entry
        ).order_by("-counter")
        if links.exists():
            for link_info in links:
                entries = LinkDataModel.objects.filter(id=link_info.entry_to.id)
                if entries.exists():
                    entry = entries[0]
                    result.append(entry)

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
                entry_from=entry_from, entry_to=entry_to, counter=1, user_object=user
            )

    def get_element(user, entry_from, entry_to):
        links = UserEntryTransitionHistory.objects.filter(
            user_object=user, entry_from=entry_from, entry_to=entry_to
        ).order_by("-counter")
        if links.exists():
            return links[0]

    def cleanup():
        config_entry = Configuration.get_object().config_entry
        if (
            not config_entry.track_user_actions
            or not config_entry.track_user_navigation
        ):
            UserEntryTransitionHistory.objects.all().delete()

        # safety cleanup, if user is not set
        qs = UserEntryTransitionHistory.objects.filter(user_object__isnull=True)
        for q in qs:
            users = User.objects.filter(username=q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.info("Cannot find user:'{}'".format(q.user))
                q.delete()
                time.sleep(0.5)

    def move_entry(source_entry, destination_entry):
        """
        We move entry from https:// to http://. We want that history to be preserved
        """
        transitions = UserEntryTransitionHistory.objects.filter(entry_from = source_entry)
        for transition in transitions:
            dst_transitions = UserEntryTransitionHistory.objects.filter(entry_from = destination_entry, user_object = transition.user_object)
            if dst_transitions.exists():
                dst_transition = dst_transitions[0]
                dst_transition.counter += transition.counter
                dst_transition.save()

                transition.delete()
                continue

            transition.entry_from = destination_entry
            transition.save()

        transitions = UserEntryTransitionHistory.objects.filter(entry_to = source_entry)
        for transition in transitions:
            dst_transitions = UserEntryTransitionHistory.objects.filter(entry_to = destination_entry, user_object = transition.user_object)
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
    user_object = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name=str(LinkDatabase.name) + "_entry_visits",
        null=True,
    )

    entry_object = models.ForeignKey(
        LinkDataModel,
        on_delete=models.CASCADE,
        related_name="visits_counter",
    )

    def visited(entry, user):
        """
        User visited a link:
         - if it is just hit before a minute (f5 etc.) do nothing
         - if we transitioned from other link store that info
         - increment visits counter
        """
        from ..configuration import Configuration
        from ..dateutils import DateUtils
        from ..controllers import BackgroundJobController

        """
        TODO to think about. are we capturing data about not logged users?
        """
        if not user.is_authenticated:
            return

        config = Configuration.get_object().config_entry

        # ignore misinformation, etc.
        if entry.get_vote() < 0:
            return

        if not config.track_user_actions or not config.track_user_navigation:
            return

        if str(user.username) == "" or user.username is None:
            return

        visits = UserEntryVisitHistory.objects.filter(
            entry_object=entry, user_object=user
        )

        if UserEntryVisitHistory.is_link_just_visited(visits):
            return

        previous_entry = UserEntryVisitHistory.get_last_user_entry(user)

        try:
            if previous_entry:
                UserEntryTransitionHistory.add(user, previous_entry, entry)

            if visits.count() == 0:
                visit = UserEntryVisitHistory.objects.create(
                    visits=1,
                    entry_object=entry,
                    date_last_visit=DateUtils.get_datetime_now_utc(),
                    user_object=user,
                )
            else:
                visit = visits[0]
                visit.visits += 1
                visit.date_last_visit = DateUtils.get_datetime_now_utc()
                visit.user_object = user
                visit.save()

            # to increment visited counter on entry
            # BackgroundJobController.entry_update_data(entry)
            # TODO - there should be recalculated JOB. we do not want to udpate it's data

            return visit

        except Exception as E:
            LinkDatabase.info(str(E))
            AppLogging.error("Could not add transition")

    def is_link_just_visited(visits):
        from ..dateutils import DateUtils

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
            user_object=user,
            entry_object=entry,
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
        from ..dateutils import DateUtils

        time_ago_limit = DateUtils.get_datetime_now_utc() - timedelta(hours=1)
        burst_time_limit = DateUtils.get_datetime_now_utc() - timedelta(seconds=15)

        entries = UserEntryVisitHistory.objects.filter(
            user_object=user,
            date_last_visit__gt=time_ago_limit,
            date_last_visit__lt=burst_time_limit,
        ).order_by("-date_last_visit")
        if entries.exists():
            return entries[0].entry_object

    def cleanup():
        config_entry = Configuration.get_object().config_entry
        if (
            not config_entry.track_user_actions
            or not config_entry.track_user_navigation
        ):
            UserEntryVisitHistory.objects.all().delete()

        # safety cleanup, if user is not set
        qs = UserEntryVisitHistory.objects.filter(user_object__isnull=True)
        for q in qs:
            users = User.objects.filter(username=q.user)
            if users.count() > 0:
                q.user_object = users[0]
                q.save()
            else:
                LinkDatabase.info("Cannot find user:'{}'".format(q.user))
                q.delete()
                time.sleep(0.5)

    def move_entry(source_entry, destination_entry):
        visits = UserEntryVisitHistory.objects.filter(entry_object = source_entry)
        for visit in visits:
            dst_visits = UserEntryVisitHistory.objects.filter(entry_object = destination_entry, user_object = visit.user_object)
            if dst_visits.exists():
                dst_visit = dst_visits[0]
                dst_visit.visits += visit.visits
                if visit.date_last_visit > dst_visit.date_last_visit:
                    dst_visit.date_last_visit = visit.date_last_visit
                dst_visit.save()

                visit.delete()
                continue

            visit.entry_object = destination_entry
            visit.save()


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
