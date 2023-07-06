
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..forms import OmniSearchProcessor
from ..models import LinkDataModel


class OmniSearchTest(TestCase):
    def test_parse_conditions(self):

        processor = OmniSearchProcessor("title == test & tag == something")
        conditions = processor.parse_conditions()

        self.assertEqual(conditions[0].data, "title")
        self.assertEqual(conditions[1].data, "==")
        self.assertEqual(conditions[2].data, "test")
        self.assertEqual(conditions[3].data, "&")
        self.assertEqual(conditions[4].data, "tag")
        self.assertEqual(conditions[5].data, "==")
        self.assertEqual(conditions[6].data, "something")

        self.assertEqual(len(conditions), 7)

    def test_parse_conditions_with_brackets(self):

        processor = OmniSearchProcessor("(title == test & tag == something)")
        conditions = processor.parse_conditions()

        self.assertEqual(conditions[0].data, "(")
        self.assertEqual(conditions[1].data, "title")
        self.assertEqual(conditions[2].data, "==")
        self.assertEqual(conditions[3].data, "test")
        self.assertEqual(conditions[4].data, "&")
        self.assertEqual(conditions[5].data, "tag")
        self.assertEqual(conditions[6].data, "==")
        self.assertEqual(conditions[7].data, "something")
        self.assertEqual(conditions[8].data, ")")

        self.assertEqual(len(conditions), 9)

    def test_get_eval(self):

        processor = OmniSearchProcessor("title == test & tag == something")
        conditions = processor.parse_conditions()

        eval_text = processor.get_eval_query(conditions[0:3])

        self.assertEqual(eval_text, {"title__contains": "test"})

    def test_filter_query_set(self):
        LinkDataModel.objects.create(link = "https://test.com")

        processor = OmniSearchProcessor('link == https://test.com')

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(len(qs)))

        qs = processor.filter_queryset(qs)
        print("Query set length: {}".format(len(qs)))

        self.assertEqual(len(qs), 1)

