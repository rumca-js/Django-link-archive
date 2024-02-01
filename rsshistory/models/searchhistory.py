"""
 - in order for any search engine to work all actions of user have to be captured
 - the causation needs to be established
 - the engine needs to know the person it tracks (does anonymization exist for search engines?)
"""

from django.db import models


class UserSearchHistory(models.Model):
    """
    Just a search history
    """

    search_query = models.CharField(max_length=1000)
    user = models.CharField(max_length=1000)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def add(user, search_query):
        if search_query is not None and search_query != "":
            if UserSearchHistory.get_top_query(user) == search_query:
                return

            UserSearchHistory.delete_old_user_entries(search_query=search_query, user=user)

            theobject = UserSearchHistory.objects.create(search_query=search_query, user=user)
            UserSearchHistory.delete_old_entries()

            return theobject

    def get_top_query(user):
        qs = UserSearchHistory.objects.filter(user=user).order_by("-date")
        if qs.exists():
            return qs[0]

    def get_user_choices(user):
        choices = []
        choices.append(["", ""])

        qs = UserSearchHistory.objects.filter(user=user).order_by("-date")
        for q in qs:
            choices.append([q.search_query, q.search_query])

        return choices

    def delete_old_entries():
        qs = UserSearchHistory.objects.all().order_by("date")
        limit = UserSearchHistory.get_choices_limit()
        if qs.count() > limit:
            too_many = qs.count() - limit
            entries = qs[:too_many]
            for entry in entries:
                entry.delete()

    def delete_old_user_entries(user, search_query):
        entries = UserSearchHistory.objects.filter(search_query=search_query, user=user)
        if entries.exists():
            entries.delete()

    def get_choices_limit():
        return 100


class EntryHitUserSearchHistory(models.Model):
    """
    User searches for something. Then clicks a link. That is a hit.
    Store it here. Match between search & hit.
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
    """

    search_query = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000, unique=True)
    vote = models.IntegerField(default=0)


class EntryRelatedHistory(models.Model):
    """
    Sometimes user goes from a link to another. Store that info.
    TODO How to rank it?
    """

    link_from = models.CharField(max_length=1000, unique=True)
    link_to = models.CharField(max_length=1000, unique=True)
    vote = models.IntegerField(default=0)
