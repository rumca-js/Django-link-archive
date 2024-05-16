from django.db.models import Q
from ..queryfilters import OmniSearchFilter, StringSymbolEquation, OmniSymbolProcessor, OmniSearchConditions, OmniSymbolEvaluator
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


class OmniSymbolProcessorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_omni_search_next_and(self):
        args = "title == test & tag == something"

        tok = OmniSymbolProcessor(args, SymbolEvaluator())
        value = tok.process()

        self.assertEqual(tok.eq_string, "A&B")
        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag == something")

        # 1 & 5 == 1
        self.assertEqual(value, 1)

    def test_omni_search_quotes(self):
        args = 'title == "test" & tag == "something"'

        tok = OmniSymbolProcessor(args, SymbolEvaluator())

        value = tok.process()

        self.assertEqual(tok.eq_string, "A&B")
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


class OmniSymbolEvaluatorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_evauluate_symbol_exact(self):
        ev = OmniSymbolEvaluator()

        ev.set_translation_mapping({"title" : "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title == something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__iexact', 'something'))")

    def test_evauluate_symbol_gte(self):
        ev = OmniSymbolEvaluator()

        ev.set_translation_mapping({"title" : "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title >= something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__gte', 'something'))")

    def test_evauluate_symbol_gt(self):
        ev = OmniSymbolEvaluator()

        ev.set_translation_mapping({"title" : "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title > something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__gt', 'something'))")

    def test_evauluate_symbol_equals(self):
        ev = OmniSymbolEvaluator()

        ev.set_translation_mapping({"title" : "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title = something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__icontains', 'something'))")

    def test_evauluate_symbol_translate_contains(self):
        ev = OmniSymbolEvaluator()

        ev.set_translation_mapping({"title" : "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title__isnull = True")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__isnull', True))")

    def test_evauluate_symbol_equals_mapping(self):
        ev = OmniSymbolEvaluator()

        ev.set_translation_mapping({"title.link" : "title_obj__link"})

        # call tested function
        sym_data = ev.evaluate_symbol("title.link = something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title.link__icontains', 'something'))")

    def test_evauluate_symbol_equals_none(self):
        ev = OmniSymbolEvaluator()

        # call tested function
        sym_data = ev.evaluate_symbol("title = something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "None")

        conditions = ev.not_translated_conditions

        self.assertTrue("title" in conditions)
        self.assertEqual(conditions["title"], "something")

    def test_evauluate_symbol_default_symbols(self):
        ev = OmniSymbolEvaluator()

        ev.set_default_search_symbols(["title__icontains", "description__icontains"])

        # call tested function
        sym_data = ev.evaluate_symbol("my test")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(OR: ('title__icontains', 'my test'), ('description__icontains', 'my test'))")


class OmniSearchConditionsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_not_translated_conditions(self):
        LinkDataModel.objects.create(link="https://test.com")

        search_query = "link == https://test.com"
        c = OmniSearchConditions(search_query)

        c.get_conditions()

        # call tested function
        conditions = c.get_not_translated_conditions()

        self.assertTrue("link" in conditions)
        self.assertEqual(conditions["link"], "https://test.com")

    def test_get_conditions_processor_evaluator(self):
        LinkDataModel.objects.create(link="https://test.com")


        search_query = "link == https://test.com"
        processor = OmniSearchConditions(search_query)

        processor.set_translation_mapping(["link"])

        # call tested function
        conditions = processor.get_conditions()

        str_conditions = str(conditions)
        self.assertEqual(str_conditions, "(AND: ('link__iexact', 'https://test.com'))")

    def test_get_conditions_default_symbols(self):
        LinkDataModel.objects.create(link="https://test.com", title="find title")

        search_query = "find title"
        processor = OmniSearchConditions(search_query)

        processor.set_translation_mapping(["link", "title"])
        processor.set_default_search_symbols(["title__icontains", "description__icontains"])

        # call tested function
        conditions = processor.get_conditions()

        str_conditions = str(conditions)
        self.assertEqual(str_conditions, "(OR: ('title__icontains', 'find title'), ('description__icontains', 'find title'))")


class OmniSearchFilterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_filtered_objects_one_property(self):
        LinkDataModel.objects.create(link="https://test1.com")
        LinkDataModel.objects.create(link="https://test2.com")

        args = {"search": "link == https://test1.com"}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translation_mapping(["link"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects_with_double_quotes(self):
        LinkDataModel.objects.create(link="https://test.com", artist="Sombody Anybody")

        args = {"search": 'artist = "Sombody "'}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translation_mapping(["link", "artist"])

        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects_with_single_quotes(self):
        LinkDataModel.objects.create(link="https://test.com", artist="Sombody Anybody")

        args = {"search": "artist = 'Sombody '"}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translation_mapping(["link", "artist"])

        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects_two_properties(self):
        LinkDataModel.objects.create(link="https://test1.com", title="One title", description="One description")
        LinkDataModel.objects.create(link="https://test2.com", title="Two title", description="Two description")

        args = {"search": "link == https://test1.com & title == One Title"}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translation_mapping(["link", "title", "description"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects_with_no_equal(self):
        LinkDataModel.objects.create(link="https://test.com", artist="Sombody Anybody")

        args = {"search": "Sombody"}
        processor = OmniSearchFilter(args)

        qs = LinkDataModel.objects.all()
        print("Query set length: {}".format(qs.count()))

        processor.set_query_set(qs)
        processor.set_translation_mapping(["link", "artist"])

        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)
