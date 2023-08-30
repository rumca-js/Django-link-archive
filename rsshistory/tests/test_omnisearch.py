from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from ..queryfilters import OmniSearchFilter, StringSymbolEquation, OmniSymbolProcessor
from ..models import LinkDataModel


class SymbolEvaluator(object):
    def evaluate_symbol(self, symbol):
        if symbol == "title == test":
            return 5
        elif symbol == "tag == something":
            return 1
        else:
            return 0


class OmniSearchTest(TestCase):
    def test_filter_query_set(self):
        LinkDataModel.objects.create(link="https://test.com")

        args = {"search": "link == https://test.com"}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)

        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_symbol_equation_1(self):
        text = "(title == test & description == none) | title == covid"

        tok = StringSymbolEquation(text)
        string, conditions = tok.process()

        self.assertEqual(string, "(A&B)|C")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "description == none")
        self.assertEqual(conditions["C"], "title == covid")

    def test_symbol_equation_2(self):
        text = "(title == test & description == none) | !(title == covid)"

        tok = StringSymbolEquation(text)
        string, conditions = tok.process()

        self.assertEqual(string, "(A&B)|!(C)")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "description == none")
        self.assertEqual(conditions["C"], "title == covid")

    def test_symbol_equation_3(self):
        text = "title == test & tag == something"

        tok = StringSymbolEquation(text)
        string, conditions = tok.process()

        self.assertEqual(string, "A&B")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "tag == something")

    def test_omni_search_next_and(self):
        args = "title == test & tag == something"

        tok = OmniSymbolProcessor(args, SymbolEvaluator())
        self.assertEqual(tok.eq_string, "A&B")

        value = tok.process()

        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag == something")

        # 1 & 5 == 1
        self.assertEqual(value, 1)

    def test_omni_search_next_or(self):
        args = "title == test | tag == something"

        tok = OmniSymbolProcessor(args, SymbolEvaluator())
        value = tok.process()

        self.assertEqual(tok.eq_string, "A|B")
        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag == something")

        # 1 | 5 == 1
        self.assertEqual(value, 5)
