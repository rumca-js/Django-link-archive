from django.db.models import Q
from django.utils.http import urlencode

from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
)
from .models import Domains

try:
    from sympy import sympify
    import sympy
except Exception as E:
    pass


class BaseQueryFilter(object):
    def __init__(self, args, page_limit=False):
        self.args = args
        self.use_page_limit = page_limit

        if "archive" in self.args and self.args["archive"] == "on":
            self.use_archive_source = True
        else:
            self.use_archive_source = False

        self.error = False

    def get_filter_string(self):
        infilters = self.args

        filter_data = {}
        for key in infilters:
            value = infilters[key]
            if key != "page" and value != "":
                filter_data[key] = value
        return "&" + urlencode(filter_data)

    def get_model_pagination(self):
        return 100

    def get_limit(self):
        if "page" in self.args:
            page = int(self.args["page"])
        else:
            page = 1

        paginate_by = self.get_model_pagination()
        # for page 1, paginate_by 100  we have range 0..99
        # for page 2, paginate_by 100  we have range 100..199

        start = (page - 1) * paginate_by

        return [start, start + paginate_by]

    def get_filtered_objects(self):
        filtered_objects = self.get_filtered_objects_internal()
        if filtered_objects is None:
            self.error = True
            return

        filtered_objects = filtered_objects.distinct()

        if self.use_page_limit:
            limit_range = self.get_limit()
            if limit_range:
                filtered_objects = filtered_objects[limit_range[0] : limit_range[1]]

        self.filtered_objects = filtered_objects

        return self.filtered_objects

    def is_error(self):
        return self.error


class SourceFilter(BaseQueryFilter):
    def __init__(self, args):
        super().__init__(args)

    def get_filtered_objects_internal(self):
        conditions = self.get_conditions()
        print("Source filter conditions: {}".format(conditions))

        if conditions:
            return SourceDataController.objects.filter(conditions)
        else:
            return SourceDataController.objects.none()

    def get_conditions(self):
        q1 = self.get_arg_conditions_query()
        q2 = self.get_omni_conditions()

        if q1 and q2:
            return q1 & q2
        if q1:
            return q1
        if q2:
            return q2

        self.error = True

    def get_omni_conditions(self):
        query_filter = OmniSearchFilter(self.args)

        translate = SourceDataController.get_query_names()
        query_filter.set_translatable(translate)

        query_filter.set_default_search_symbols(
            [
                "title__icontains",
            ]
        )

        query_filter.calculate_combined_query()
        return query_filter.combined_query

    def get_arg_conditions_query(self):
        args = self.get_arg_conditions(True)
        return Q(**args)

    def get_arg_conditions(self, translate=False):
        parameter_map = {}

        category = self.args.get("category")
        if category and category != "":
            parameter_map["category"] = category

        subcategory = self.args.get("subcategory")
        if subcategory and subcategory != "":
            parameter_map["subcategory"] = subcategory

        title = self.args.get("title")
        if title and title != "":
            parameter_map["title"] = title

        return parameter_map

    def get_model_pagination(self):
        from .viewspkg.viewsources import RssSourceListView

        return int(RssSourceListView.paginate_by)


class EntryFilter(BaseQueryFilter):
    def __init__(self, args):
        super().__init__(args)
        self.time_constrained = True

        self.use_archive_source = False
        self.additional_condition = Q()

    def get_model_pagination(self):
        from .viewspkg.viewentries import EntriesSearchListView

        return int(EntriesSearchListView.paginate_by)

    def get_filtered_objects_internal(self):
        conditions = self.get_conditions()
        print(conditions)

        if not conditions:
            return LinkDataController.objects.none()

        if not self.use_archive_source:
            self.filtered_objects = LinkDataController.objects.filter(conditions)
        else:
            self.filtered_objects = ArchiveLinkDataController.objects.filter(conditions)

        return self.filtered_objects

    def get_conditions(self):
        q1 = self.get_arg_conditions_query()
        q2 = self.get_omni_conditions()
        q3 = self.additional_condition

        if q1 and q2:
            return q1 & q2 & q3
        if q1:
            return q1 & q3
        if q2:
            return q2 & q3

        self.error = True

    def get_omni_conditions(self):
        query_filter = OmniSearchFilter(self.args)

        translate = LinkDataController.get_query_names()
        query_filter.set_translatable(translate)

        query_filter.set_default_search_symbols(
            [
                "title__icontains",
                "description__icontains",
                "tags__tag__icontains",
            ]
        )

        query_filter.calculate_combined_query()
        return query_filter.combined_query

    def get_arg_conditions_query(self):
        args = self.get_arg_conditions(True)
        return Q(**args)

    def get_sources(self):
        self.sources = SourceDataController.objects.all()

    def set_time_constrained(self, constrained):
        self.time_constrained = constrained

    def set_archive_source(self, source):
        self.use_archive_source = source

    def set_additional_condition(self, condition):
        self.additional_condition = condition

    def get_hard_query_limit(self):
        10000

    def get_arg_conditions(self, translate=False):
        parameter_map = {}

        if not translate:
            self.copy_if_is_set(parameter_map, self.args, "title")
            self.copy_if_is_set(parameter_map, self.args, "language")
            self.copy_if_is_set(parameter_map, self.args, "user")
            self.copy_if_is_set(parameter_map, self.args, "tag")
            self.copy_if_is_set(parameter_map, self.args, "vote")
            self.copy_if_is_set(parameter_map, self.args, "source_title")
            self.copy_if_is_set(parameter_map, self.args, "bookmarked")
            self.copy_if_is_set(parameter_map, self.args, "category")
            self.copy_if_is_set(parameter_map, self.args, "subcategory")
            self.copy_if_is_set(parameter_map, self.args, "artist")
            self.copy_if_is_set(parameter_map, self.args, "album")
            self.copy_if_is_set(parameter_map, self.args, "date_from")
            self.copy_if_is_set(parameter_map, self.args, "date_to")
            self.copy_if_is_set(parameter_map, self.args, "archive")

            if self.time_constrained:
                date_range = self.get_default_range()
                if "date_from" not in parameter_map:
                    parameter_map["date_from"] = date_range[0]
                if "date_to" not in parameter_map:
                    parameter_map["date_to"] = date_range[1]

            return parameter_map
        else:
            self.copy_if_is_set_and_translate(parameter_map, self.args, "title")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "language")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "user")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "tag")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "vote")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "source_title")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "bookmarked")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "category")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "subcategory")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "artist")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "album")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "date_from")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "date_to")

            if self.time_constrained:
                if "date_published__range" not in parameter_map:
                    date_range = self.get_default_range()
                    parameter_map["date_published__range"] = [
                        date_range[0],
                        date_range[1],
                    ]

        return parameter_map

    def copy_if_is_set_and_translate(self, dst, src, element):
        if element in src and src[element] != "":
            if element == "title":
                dst["title__icontains"] = src[element]
            elif element == "language":
                dst["language__icontains"] = src[element]
            elif element == "category":
                dst["source_obj__category"] = src[element]
            elif element == "subcategory":
                dst["source_obj__subcategory"] = src[element]
            elif element == "source_title":
                dst["source_obj__title"] = src[element]
            elif element == "user":
                dst["user__icontains"] = src[element]
            elif element == "bookmarked":
                if src[element] == "on":
                    dst["bookmarked"] = True
                else:
                    dst["bookmarked"] = False
            elif element == "tag":
                if src[element].startswith('"'):
                    dst["tags__tag"] = src[element][1:-1]
                else:
                    dst["tags__tag__icontains"] = src[element]
            elif element == "vote":
                dst["votes__vote__gt"] = src[element]
            elif element == "date_from":
                if "date_to" in src and src["date_to"] != "":
                    dst["date_published__range"] = [
                        src["date_from"],
                        src["date_to"],
                    ]
            elif element == "date_to":
                pass
            elif element == "artist":
                dst["artist__icontains"] = src[element]
            elif element == "album":
                dst["album__icontains"] = src[element]
            else:
                dst[element] = src[element]

    def get_default_range(self):
        from .dateutils import DateUtils

        return DateUtils.get_days_range()

    def copy_if_is_set(self, dst, src, element):
        if element in src and src[element] != "":
            dst[element] = src[element]


class DomainFilter(BaseQueryFilter):
    def __init__(self, args):
        super().__init__(args)

    def get_filtered_objects_internal(self):
        conditions = self.get_conditions()
        print(conditions)

        self.filtered_objects = Domains.objects.filter(conditions)

        return self.filtered_objects

    def get_conditions(self):
        return self.get_arg_conditions_query() & self.get_omni_conditions()

    def get_omni_conditions(self):
        query_filter = OmniSearchFilter(self.args)

        translate = Domains.get_query_names()
        query_filter.set_translatable(translate)

        query_filter.set_default_search_symbols(
            [
                "domain__icontains",
                "title__icontains",
                "description__icontains",
            ]
        )

        query_filter.calculate_combined_query()
        return query_filter.combined_query

    def get_arg_conditions_query(self):
        args = self.get_arg_conditions(True)
        return Q(**args)

    def get_arg_conditions(self, translate=False):
        parameter_map = {}

        suffix = self.args.get("suffix")
        if suffix and suffix != "":
            parameter_map["suffix"] = suffix

        tld = self.args.get("tld")
        if tld and tld != "":
            parameter_map["tld"] = tld

        main = self.args.get("main")
        if main and main != "":
            parameter_map["main"] = main

        domain = self.args.get("domain")
        if domain and domain != "":
            parameter_map["domain__icontains"] = domain

        return parameter_map


class StringSymbolEquation(object):
    def __init__(self, data):
        self.data = data
        self.current_symbol = ord("A") - 1

    def get_operators():
        return ("(", ")", "&", "|", "~", "^", "!")

    def get_whitespaces():
        return (" ", "\t")

    def is_operator(char):
        return char in StringSymbolEquation.get_operators()

    def is_whitespace(char):
        return char in StringSymbolEquation.get_whitespaces()

    def process(self):
        result_string = ""
        inside_text = False
        self.conditions = {}
        self.current_condition = ""

        for char in self.data:
            if StringSymbolEquation.is_operator(char):
                inside_text = False
                result_string += char

                self.add_condition()

            elif inside_text:
                self.current_condition += char
            else:
                self.current_condition += char

                if not StringSymbolEquation.is_whitespace(char):
                    inside_text = True
                    result_string += self.get_next_symbol()

        self.add_condition()

        return result_string, self.conditions

    def add_condition(self):
        self.current_condition = self.current_condition.strip()
        if self.current_condition != "":
            self.conditions[self.get_current_symbol()] = self.current_condition
            self.current_condition = ""

    def get_current_symbol(self):
        return chr(self.current_symbol)

    def get_next_symbol(self):
        self.current_symbol += 1
        return chr(self.current_symbol)


class OmniSymbolProcessor(object):
    def __init__(self, data, symbol_evaluator):
        self.symbol_evaluator = symbol_evaluator
        self.known_results = {}

        self.translate_to_symbol_notation(data)
        self.expr = sympify(self.eq_string)

    def translate_to_symbol_notation(self, data):
        eq = StringSymbolEquation(data)
        self.eq_string, self.conditions = eq.process()

    def process(self):
        return self.process_internal(self.expr)

    def process_internal(self, expr):
        for arg in expr.args:
            self.process_internal(arg)

        if expr.func == sympy.core.symbol.Symbol:
            symbol = str(expr)

            return self.evaluate_symbol(symbol)
        else:
            function = str(expr.func)
            operation_symbol = str(expr)
            print("Operation: {}".format(function))

            return self.make_operation(operation_symbol, function, expr.args)

        # print(f'arg {expr}')
        # print(f'arg.func: {expr.func}')
        # print(f'arg.args: {expr.args}')

    def evaluate_symbol(self, symbol):
        condition_text = self.conditions[symbol]
        print("Evaluation condition {} {}".format(symbol, condition_text))

        self.known_results[symbol] = self.symbol_evaluator.evaluate_symbol(
            condition_text
        )

        return self.known_results[symbol]

    def make_operation(self, operation_symbol, function, args):
        args0 = str(args[0])
        args0 = self.known_results[args0]

        if len(args) > 1:
            args1 = str(args[1])
            args1 = self.known_results[args1]
        else:
            args1 = None

        print(
            "Evaluation function: full:{} function:{} args:{} {}".format(
                operation_symbol, function, args0, args1
            )
        )

        if function == "And": # & sign
            self.known_results[operation_symbol] = args0 & args1
            return self.known_results[operation_symbol]
        elif function == "Or": # | sign
            self.known_results[operation_symbol] = args0 | args1
            return self.known_results[operation_symbol]
        elif function == "Not": # ~ sign
            self.known_results[operation_symbol] = ~args0
            return self.known_results[operation_symbol]
        else:
            raise NotImplementedError("Not implemented function: {}".format(function))


class OmniSymbolEvaluator(object):
    def __init__(self):
        self.fields = {}
        self.default_search_symbols = []
        self.translatable_names = []

    def evaluate_symbol(self, symbol):
        condition_data = self.split_symbol(symbol)
        if condition_data:
            print("Condition data {}".format(condition_data))

            if self.is_translatable(condition_data):
                condition_data = self.translate_condition(condition_data)

                print("Symbol evaluator condition data:{}".format(condition_data))
                return Q(**condition_data)
            else:
                self.fields[condition_data[0]] = condition_data[2]
        else:
            if not symbol or symbol == "":
                return

            result = None
            for item in self.default_search_symbols:
                input_map = {item: symbol}

                if result is None:
                    result = Q(**input_map)
                else:
                    result |= Q(**input_map)

            return result

    def get_operators(self):
        return ("==", "=", "~", "<=", ">=", "<", ">", "is null")

    def cleanup_left_operator_part(self, left_part):
        return left_part.strip()

    def cleanup_right_operator_part(self, right_part):
        right_part = right_part.strip()

        wh1 = right_part.find('"')
        wh2 = right_part.find('"', wh1+1)

        if wh1 == 0 and wh2 == len(right_part) - 1:
            right_part = right_part[1:-1]

        return right_part

    def split_symbol(self, symbol):
        for op in self.get_operators():
            sp = symbol.split(op)
            if len(sp) > 1:
                left_part = self.cleanup_left_operator_part(sp[0])
                right_part = self.cleanup_right_operator_part(sp[1])

                return [left_part, op, right_part]

        wh = symbol.find("is null")
        if wh >= 0:
            return [symbol[:wh].strip(), "is null", ""]

    def is_translatable(self, condition):
        return condition[0] in self.translatable_names

    def translate_condition(self, condition_data):
        """
        https://docs.djangoproject.com/en/4.2/ref/models/querysets/#field-lookups
        """

        if condition_data[1] == "==":
            return {condition_data[0] + "__iexact": condition_data[2]}
        elif condition_data[1] == "=":
            return {condition_data[0] + "__icontains": condition_data[2]}
        elif condition_data[1] == ">":
            return {condition_data[0] + "__gt": condition_data[2]}
        elif condition_data[1] == "<":
            return {condition_data[0] + "__lt": condition_data[2]}
        elif condition_data[1] == ">=":
            return {condition_data[0] + "__gte": condition_data[2]}
        elif condition_data[1] == "<=":
            return {condition_data[0] + "__lte": condition_data[2]}
        elif condition_data[1] == "is null":
            return {condition_data[0] + "__isnull": True}

    def is_archive_source(self):
        return False

    def set_default_search_symbols(self, symbols):
        self.default_search_symbols = symbols

    def set_translatable(self, names):
        self.translatable_names = names


class OmniSearchFilter(BaseQueryFilter):
    def __init__(self, args):
        super().__init__(args)

        if "search" in self.args:
            self.data = self.args["search"]
        else:
            self.data = ""

        self.query_set = None
        self.default_search_symbols = []
        self.translatable_names = []
        self.combined_query = None

        self.symbol_evaluator = OmniSymbolEvaluator()

    def set_query_set(self, query_set):
        self.query_set = query_set

    def set_default_search_symbols(self, symbols):
        self.default_search_symbols = symbols

    def set_translatable(self, names):
        self.translatable_names = names

    def get_fields(self):
        return self.symbol_evaluator.fields

    def calculate_combined_query(self):
        uses_operator = False

        operators = set()
        for symbol in self.symbol_evaluator.get_operators():
            operators.add(symbol)
        for symbol in StringSymbolEquation.get_operators():
            operators.add(symbol)

        for symbol in operators:
            if self.data.find(symbol) >= 0:
                uses_operator = True
                break

        if uses_operator:
            try:
                self.combined_query = self.get_combined_query_using_processor()
            except Exception as e:
                self.combined_query = Q()
        else:
            self.combined_query = self.get_combined_query_simple()

    def get_combined_query_simple(self):
        symbol = self.data

        if not symbol or symbol == "":
            return Q()

        result = None
        for item in self.default_search_symbols:
            input_map = {item: symbol}

            if result is None:
                result = Q(**input_map)
            else:
                result |= Q(**input_map)

        return result

    def get_combined_query_using_processor(self):
        self.symbol_evaluator.set_default_search_symbols(self.default_search_symbols)
        self.symbol_evaluator.set_translatable(self.translatable_names)

        if self.data:
            proc = OmniSymbolProcessor(self.data, self.symbol_evaluator)
            combined_q_object = proc.process()
            return combined_q_object

    def get_filtered_objects_internal(self):
        if self.query_set is None:
            return []

        if self.data is not None and self.data != "":
            self.calculate_combined_query()

            filtered_queryset = self.query_set.filter(self.combined_query).distinct()
            print("Omni query:{}".format(filtered_queryset))
            print("Omni query:{}".format(filtered_queryset.query))
            return filtered_queryset
        else:
            return self.query_set
