from ..queryfilters import OmniSearchFilter, StringSymbolEquation, OmniSymbolProcessor
from ..models import LinkDataModel

from .fakeinternet import FakeInternetTestCase


class SymbolEvaluator(object):
    def evaluate_symbol(self, symbol):
        if symbol == "title == test":
            return 5
        elif symbol == "tag == something":
            return 1
        elif symbol == 'tag == "something"':
            return 2
        elif symbol == 'title == "test"':
            return 6
        else:
            return 0


class OmniSearchFilterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_filter_query_set_not_translable(self):
        LinkDataModel.objects.create(link="https://test.com")

        args = {"search": "link == https://test.com"}
        processor = OmniSearchFilter(args)

        processor.calculate_combined_query()
        fields = processor.get_fields()

        # link is not translatable. can be read by fields

        self.assertTrue("link" in fields)
        self.assertEqual(fields["link"], "https://test.com")

    def test_filter_query_set(self):
        LinkDataModel.objects.create(link="https://test.com")

        args = {"search": "link == https://test.com"}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translatable(["link"])

        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_filter_query_set_with_double_quotes(self):
        LinkDataModel.objects.create(link="https://test.com", artist="Sombody Anybody")

        args = {"search": 'artist = "Sombody "'}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translatable(["link", "artist"])

        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_filter_query_set_with_single_quotes(self):
        LinkDataModel.objects.create(link="https://test.com", artist="Sombody Anybody")

        args = {"search": "artist = 'Sombody '"}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translatable(["link", "artist"])

        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)


class OmniSearchEquationTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

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

    def test_symbol_equation_3_double_quotes(self):
        text = 'title == test & tag == "something"'

        tok = StringSymbolEquation(text)
        string, conditions = tok.process()

        self.assertEqual(string, "A&B")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], 'tag == "something"')

    def test_symbol_equation_3_single_quotes(self):
        text = "title == test & tag == 'something'"

        tok = StringSymbolEquation(text)
        string, conditions = tok.process()

        self.assertEqual(string, "A&B")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "tag == 'something'")


class OmniSearchProcessorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_omni_search_next_and(self):
        args = "title == test & tag == something"

        tok = OmniSymbolProcessor(args, SymbolEvaluator())
        self.assertEqual(tok.eq_string, "A&B")

        value = tok.process()

        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag == something")

        # 1 & 5 == 1
        self.assertEqual(value, 1)

    def test_omni_search_quotes(self):
        args = 'title == "test" & tag == "something"'

        tok = OmniSymbolProcessor(args, SymbolEvaluator())
        self.assertEqual(tok.eq_string, "A&B")

        value = tok.process()

        self.assertEqual(tok.conditions["A"], 'title == "test"')
        self.assertEqual(tok.conditions["B"], 'tag == "something"')

        # 2 & 6 == 2
        self.assertEqual(value, 2)

    def test_omni_search_next_or(self):
        args = "title == test | tag == something"

        tok = OmniSymbolProcessor(args, SymbolEvaluator())
        value = tok.process()

        self.assertEqual(tok.eq_string, "A|B")
        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag == something")

        # 1 | 5 == 1
        self.assertEqual(value, 5)
