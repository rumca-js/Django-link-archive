
from ..models import UserSearchHistory
from django.test import TestCase


class PageSystemPageTest(TestCase):

    def test_add(self):
        # call tested function
        theobject = UserSearchHistory.add("test_user1", "query1")

        objects = UserSearchHistory.objects.all()

        self.assertEqual(objects.count(), 1)
        self.assertEqual(objects[0], theobject)

    def test_more_than_limit(self):
        for index in range(1, 102):
            user = "test_user{}".format(index)
            query = "query{}".format(index)
            #print("User:{} Query:{}".format(user, query))

            # call tested function
            UserSearchHistory.add(user, query)

        objects = UserSearchHistory.objects.all()

        self.assertEqual(objects.count(), UserSearchHistory.get_choices_limit())
