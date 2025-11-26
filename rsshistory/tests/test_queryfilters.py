from django.contrib.auth.models import User
from django.db.models import Q

from utils.dateutils import DateUtils

from ..controllers import SourceDataController, LinkDataController
from ..queryfilters import (
    SourceFilter,
    EntryFilter,
    OmniSearchFilter,
    DjangoSingleSymbolEvaluator,
    OmniSearchWithDefault,
    DjangoEquationProcessor,
)

from .fakeinternet import FakeInternetTestCase


class FiltersTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category_name="No",
            subcategory_name="No",
            export_to_cms=True,
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source_url="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category_name="No",
            subcategory_name="No",
            export_to_cms=False,
        )

        self.user = User.objects.create_user(
            username="TestUser", password="testpassword", is_staff=True
        )

    def test_source_arg_conditions(self):
        args = {
            "title": "link",
            "category_name": "none",
            "subcategory_name": "none",
            "notsupported": "none",
        }

        thefilter = SourceFilter(args, user=self.user)

        filter_args = thefilter.get_args_filter_map()

        self.assertTrue("title" in filter_args)
        self.assertTrue("category_name" in filter_args)
        self.assertTrue("subcategory_name" in filter_args)

        self.assertTrue("unsupported" not in filter_args)

    def test_entry_filters(self):
        args = {
            "title": "link",
            "language": "none",
            "tag__tag": "none",
            "bookmarked": "none",
            "author": "none",
            "album": "none",
            "date_published__gt": "none",
            "unsupported": "none",
        }

        thefilter = EntryFilter(args, user=self.user)

        filter_args = thefilter.get_args_filter_map()

        self.assertTrue("title" in filter_args)
        self.assertTrue("language" in filter_args)
        self.assertTrue("bookmarked" in filter_args)
        self.assertTrue("author" in filter_args)
        self.assertTrue("album" in filter_args)
        self.assertTrue("date_published__gt" in filter_args)

        self.assertTrue("unsupported" not in filter_args)

    def test_entry_filters__foreign(self):
        args = {
            "title__icontains": "link",
            "language": "none",
            "bookmarked": "none",
            "author": "none",
            "album": "none",
            "tags__tag": "none",
            "user__username": "none",
            "votes__vote__gt": "none",
            "source__title": "none",
            "unsupported": "none",
        }

        thefilter = EntryFilter(args, user=self.user)

        filter_args = thefilter.get_args_filter_map()

        self.assertTrue("title__icontains" in filter_args)
        self.assertTrue("language" in filter_args)
        self.assertTrue("bookmarked" in filter_args)
        self.assertTrue("author" in filter_args)
        self.assertTrue("album" in filter_args)
        self.assertTrue("tags__tag" in filter_args)
        self.assertTrue("user__username" in filter_args)
        self.assertTrue("votes__vote__gt" in filter_args)
        self.assertTrue("source__title" in filter_args)
        self.assertTrue("tags__tag" in filter_args)

        self.assertTrue("unsupported" not in filter_args)

    def test_source_filter_limit(self):
        args = {
            "title": "link",
            "category_name": "none",
            "subcategory_name": "none",
            "notsupported": "none",
            "page": "1",
        }

        thefilter = SourceFilter(args, user=self.user)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 100)

        args = {
            "title": "link",
            "category_name": "none",
            "subcategory_name": "none",
            "notsupported": "none",
            "page": "2",
        }

        thefilter = SourceFilter(args, user=self.user)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 100)
        self.assertEqual(limit[1], 200)

    def test_entry_filter_limit(self):
        args = {
            "title": "link",
            "category_name": "none",
            "subcategory_name": "none",
            "notsupported": "none",
            "page": "1",
        }

        thefilter = EntryFilter(args, user=self.user)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 100)

        args = {
            "title": "link",
            "category_name": "none",
            "subcategory_name": "none",
            "notsupported": "none",
            "page": "2",
        }

        thefilter = EntryFilter(args, user=self.user)
        limit = thefilter.get_limit()

        self.assertEqual(limit[0], 100)
        self.assertEqual(limit[1], 200)


class DjangoSingleSymbolEvaluatorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_evaluate_symbol_exact(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title": "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title === something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__iexact', 'something'))")

    def test_evaluate_symbol_eq(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title": "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title == something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title', 'something'))")

    def test_evauluate_symbol_no_space(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title": "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title==something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title', 'something'))")

    def test_evauluate_symbol_gte(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title": "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title >= something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__gte', 'something'))")

    def test_evauluate_symbol_gt(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title": "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title > something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__gt', 'something'))")

    def test_evauluate_symbol_equals(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title": "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title = something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__icontains', 'something'))")

    def test_evauluate_symbol_translate_contains(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title": "title"})

        # call tested function
        sym_data = ev.evaluate_symbol("title__isnull = True")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title__isnull', True))")

    def test_evauluate_symbol_equals_mapping(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping({"title.link": "title_obj__link"})

        # call tested function
        sym_data = ev.evaluate_symbol("title.link = something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "(AND: ('title.link__icontains', 'something'))")

    def test_evauluate_symbol_equals_none(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_translation_mapping(["nottitle"])

        # call tested function
        sym_data = ev.evaluate_symbol("title = something")

        str_sym_data = str(sym_data)
        self.assertEqual(str_sym_data, "None")

        conditions = ev.not_translated_conditions

        self.assertTrue("title" in conditions)
        self.assertEqual(conditions["title"], "something")

    def test_evauluate_symbol_default_symbols(self):
        ev = DjangoSingleSymbolEvaluator()

        ev.set_default_search_symbols(["title__icontains", "description__icontains"])

        # call tested function
        sym_data = ev.evaluate_symbol("my test")

        str_sym_data = str(sym_data)
        self.assertEqual(
            str_sym_data,
            "(OR: ('title__icontains', 'my test'), ('description__icontains', 'my test'))",
        )


class OmniSearchWithDefaultTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_not_translated_conditions(self):
        LinkDataController.objects.create(link="https://test.com")

        search_query = "link == https://test.com"
        c = OmniSearchWithDefault(search_query, DjangoSingleSymbolEvaluator())

        c.set_translation_mapping(["something"])

        c.get_query_result()

        # call tested function
        conditions = c.get_not_translated_conditions()

        self.assertTrue("link" in conditions)
        self.assertEqual(conditions["link"], "https://test.com")

        errors = c.get_errors()
        print(errors)

        self.assertEqual(len(errors), 2)
        self.assertIn("Could not calculate query", errors)
        self.assertIn("Cannot evaluate symbol:link == https://test.com", errors)

    def test_get_query_result__processor_evaluator__eq(self):
        LinkDataController.objects.create(link="https://test.com")

        search_query = "link == https://test.com"
        processor = OmniSearchWithDefault(search_query, DjangoSingleSymbolEvaluator())

        processor.set_translation_mapping(["link"])

        # call tested function
        conditions = processor.get_query_result()

        str_conditions = str(conditions)
        self.assertEqual(str_conditions, "(AND: ('link', 'https://test.com'))")

    def test_get_query_result__processor_evaluator__exact(self):
        LinkDataController.objects.create(link="https://test.com")

        search_query = "link === https://test.com"
        processor = OmniSearchWithDefault(search_query, DjangoSingleSymbolEvaluator())

        processor.set_translation_mapping(["link"])

        # call tested function
        conditions = processor.get_query_result()

        str_conditions = str(conditions)
        self.assertEqual(str_conditions, "(AND: ('link__iexact', 'https://test.com'))")

    def test_get_query_result__default_symbols(self):
        LinkDataController.objects.create(link="https://test.com", title="find title")

        search_query = "find title"
        processor = OmniSearchWithDefault(search_query, DjangoSingleSymbolEvaluator())

        processor.set_translation_mapping(["link", "title"])
        processor.set_default_search_symbols(
            ["title__icontains", "description__icontains"]
        )

        # call tested function
        conditions = processor.get_query_result()

        str_conditions = str(conditions)
        self.assertEqual(
            str_conditions,
            "(OR: ('title__icontains', 'find title'), ('description__icontains', 'find title'))",
        )


class DjangoEquationProcessorTest(FakeInternetTestCase):

    def setUp(self):
        self.disable_web_pages()

    def test_get_conditions__normal(self):
        search_query = "link === https://test.com"

        processor = DjangoEquationProcessor(search_query)

        # call tested function
        conditions = processor.get_conditions()

        str_conditions = str(conditions)
        self.assertEqual(str_conditions, "(AND: ('link__iexact', 'https://test.com'))")

    def test_get_conditions__empty(self):
        search_query = ""

        processor = DjangoEquationProcessor(search_query)

        # call tested function
        conditions = processor.get_conditions()

        self.assertEqual(conditions, Q())

    def test_get_conditions__none(self):
        search_query = None

        processor = DjangoEquationProcessor(search_query)

        # call tested function
        conditions = processor.get_conditions()

        self.assertEqual(conditions, Q())


class OmniSearchFilterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_get_filtered_objects__one_property(self):
        LinkDataController.objects.create(link="https://test1.com")
        LinkDataController.objects.create(link="https://test2.com")

        qs = LinkDataController.objects.all()
        print("Query set length: {}".format(qs.count()))

        args = {"search": "link == https://test1.com"}
        processor = OmniSearchFilter(args, init_objects=qs)
        processor.set_translation_mapping(["link"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects__with_double_quotes(self):
        LinkDataController.objects.create(
            link="https://test.com", author="Sombody Anybody"
        )

        qs = LinkDataController.objects.all()
        print("Query set length: {}".format(qs.count()))

        args = {"search": 'author = "Sombody "'}
        processor = OmniSearchFilter(args, init_objects=qs)

        processor.set_translation_mapping(["link", "author"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects__with_single_quotes(self):
        LinkDataController.objects.create(
            link="https://test.com", author="Sombody Anybody"
        )

        qs = LinkDataController.objects.all()
        print("Query set length: {}".format(qs.count()))

        args = {"search": "author = 'Sombody '"}
        processor = OmniSearchFilter(args, init_objects=qs)

        processor.set_translation_mapping(["link", "author"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects__two_properties(self):
        LinkDataController.objects.create(
            link="https://test1.com", title="One title", description="One description"
        )
        LinkDataController.objects.create(
            link="https://test2.com", title="Two title", description="Two description"
        )

        qs = LinkDataController.objects.all()
        print("Query set length: {}".format(qs.count()))

        args = {"search": "link === https://test1.com & title === One Title"}
        processor = OmniSearchFilter(args, init_objects=qs)

        processor.set_translation_mapping(["link", "title", "description"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects__default_search(self):
        LinkDataController.objects.create(
            link="https://test.com", author="Sombody Anybody"
        )

        qs = LinkDataController.objects.all()
        print("Query set length: {}".format(qs.count()))

        args = {"search": "Sombody"}
        processor = OmniSearchFilter(args, init_objects=qs)

        processor.set_default_search_symbols(["link__contains", "author__contains"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        print(processor.get_errors())

        self.assertEqual(len(processor.get_errors()), 0)
        self.assertEqual(qs.count(), 1)

    def test_get_filtered_objects__with_error_search(self):
        LinkDataController.objects.create(
            link="https://test.com", author="Sombody Anybody"
        )

        qs = LinkDataController.objects.all()
        print("Query set length: {}".format(qs.count()))

        # incorrect property
        args = {"search": "linkx==test.com"}
        processor = OmniSearchFilter(args, init_objects=qs)

        processor.set_translation_mapping(["link", "author"])

        # call tested function
        qs = processor.get_filtered_objects()
        print("Query set length: {}".format(qs.count()))

        errors = processor.get_errors()
        print(errors)

        self.assertEqual(qs.count(), 0)

        self.assertEqual(len(errors), 2)
        self.assertIn("Could not calculate query", errors)
        self.assertIn("Cannot evaluate symbol:linkx==test.com", errors)
