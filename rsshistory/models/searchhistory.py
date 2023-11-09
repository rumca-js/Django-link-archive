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

    def add(user, search_query):
        UserSearchHistory.objects.create(search_query = search_query, user=user)


class EntryHitUserSearchHistory(models.Model):
    """
    User searches for something. Then clicks a link. That is a hit.
    Store it here. Match between search & hit.
    """

    search_query = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000, unique=True)
    user = models.CharField(max_length=1000)

    def add(user, search_query, link):
        UserSearchHistory.objects.create(search_query = search_query, user=user, link=link)


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
