from django.db.models import Q
from datetime import datetime, timedelta

from ..models import SearchView

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SearchViewTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_conditions__date_published(self):
        search_view = SearchView.objects.create(
            name="test",
            filter_statement="",
            order_by="-date_published, link",
            date_published_day_limit=3,
            date_created_day_limit=0,
        )

        # call tested function
        conditions = search_view.get_conditions()
        str_conditions = str(conditions)

        start = "(AND: ('date_published__gt', datetime.datetime("
        self.assertTrue(str_conditions.find(start) >= 0)

    def test_get_conditions__date_created(self):
        search_view = SearchView.objects.create(
            name="test",
            filter_statement="",
            order_by="-date_published, link",
            date_published_day_limit=0,
            date_created_day_limit=4,
        )

        # call tested function
        conditions = search_view.get_conditions()
        str_conditions = str(conditions)

        start = "(AND: ('date_created__gt', datetime.datetime("
        self.assertTrue(str_conditions.find(start) >= 0)

    def test_get_conditions__bookmarked(self):
        search_view = SearchView.objects.create(
            name="test",
            filter_statement="bookmarked==True",
            order_by="-date_published, link",
            date_published_day_limit=0,
            date_created_day_limit=0,
        )

        # call tested function
        conditions = search_view.get_conditions()

        expected_conditions = Q(bookmarked="True")

        self.assertEqual(conditions, expected_conditions)

    def test_reset_priority(self):
        SearchView.objects.all().delete()

        search_view = SearchView.objects.create(
            name="test",
            filter_statement="bookmarked==True",
            order_by="-date_published, link",
            date_published_day_limit=0,
            date_created_day_limit=0,
        )

        # call tested function
        self.assertEqual(search_view.reset_priority(), 0)

        search_view = SearchView.objects.create(
            name="test2",
            filter_statement="bookmarked==False",
            order_by="-date_published, link",
            date_published_day_limit=0,
            date_created_day_limit=0,
        )

        # call tested function
        self.assertEqual(search_view.reset_priority(), 1)
