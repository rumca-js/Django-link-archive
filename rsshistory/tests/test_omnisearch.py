from utils.omnisearch import (
    EquationTranslator,
    EquationEvaluator,
    SingleSymbolEvaluator,
    OmniSearch,
)

from .fakeinternet import FakeInternetTestCase


class SymbolEvaluator(SingleSymbolEvaluator):
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


class EquationTranslatorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_symbol_equation_1(self):
        text = "(title == test & description == none) | title == covid"

        tok = EquationTranslator(text)
        string, conditions = tok.process()

        self.assertEqual(string, "(A&B)|C")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "description == none")
        self.assertEqual(conditions["C"], "title == covid")

    def test_symbol_equation_2(self):
        text = "(title == test & description == none) | !(title == covid)"

        tok = EquationTranslator(text)
        string, conditions = tok.process()

        self.assertEqual(string, "(A&B)|!(C)")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "description == none")
        self.assertEqual(conditions["C"], "title == covid")

    def test_symbol_equation_3(self):
        text = "title == test & tag == something"

        tok = EquationTranslator(text)
        string, conditions = tok.process()

        self.assertEqual(string, "A&B")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "tag == something")

    def test_symbol_equation_3_double_quotes(self):
        text = 'title == test & tag == "something"'

        tok = EquationTranslator(text)
        string, conditions = tok.process()

        self.assertEqual(string, "A&B")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], 'tag == "something"')

    def test_symbol_equation_3_single_quotes(self):
        text = "title == test & tag == 'something'"

        tok = EquationTranslator(text)
        string, conditions = tok.process()

        self.assertEqual(string, "A&B")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "tag == 'something'")

    def test_symbol__no_equation(self):
        text = "title == test & tag"

        tok = EquationTranslator(text)
        string, conditions = tok.process()

        self.assertEqual(string, "A&B")
        self.assertEqual(conditions["A"], "title == test")
        self.assertEqual(conditions["B"], "tag")


class EquationEvaluatorTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_omni_search_next_and(self):
        args = "title == test & tag == something"

        tok = EquationEvaluator(args, SymbolEvaluator())
        value = tok.process()

        self.assertEqual(tok.eq_string, "A&B")
        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag == something")

        # 1 & 5 == 1
        self.assertEqual(value, 1)

    def test_omni_search_quotes(self):
        args = 'title == "test" & tag == "something"'

        tok = EquationEvaluator(args, SymbolEvaluator())

        value = tok.process()

        self.assertEqual(tok.eq_string, "A&B")
        self.assertEqual(tok.conditions["A"], 'title == "test"')
        self.assertEqual(tok.conditions["B"], 'tag == "something"')

        # 2 & 6 == 2
        self.assertEqual(value, 2)

    def test_omni_search_next_or(self):
        args = "title == test | tag == something"

        tok = EquationEvaluator(args, SymbolEvaluator())
        value = tok.process()

        self.assertEqual(tok.eq_string, "A|B")
        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag == something")

        # 1 | 5 == 1
        self.assertEqual(value, 5)

    def test_omni_search__noequal(self):
        args = "title == test | tag"

        tok = EquationEvaluator(args, SymbolEvaluator())
        value = tok.process()

        self.assertEqual(tok.eq_string, "A|B")
        self.assertEqual(tok.conditions["A"], "title == test")
        self.assertEqual(tok.conditions["B"], "tag")

        # 1 | 0 == 1
        self.assertEqual(value, 5)
