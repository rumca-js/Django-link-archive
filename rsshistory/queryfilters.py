import traceback
from django.db.models import Q
from django.utils.http import urlencode

from utils.omnisearch import SingleSymbolEvaluator, OmniSearch

from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    DomainsController,
)
from .apps import LinkDatabase
from .models import UserConfig, AppLogging
from .views import get_search_term


class DjangoSingleSymbolEvaluator(SingleSymbolEvaluator):
    def __init__(self):
        super().__init__()
        self.default_search_symbols = []

        self.django_operators = []
        self.django_operators.append("isnull")
        self.django_operators.append("iexact")
        self.django_operators.append("icontains")
        self.django_operators.append("gte")
        self.django_operators.append("lte")
        self.django_operators.append("gt")
        self.django_operators.append("lt")
        self.django_operators.append("range")

    def evaluate_complex_symbol(self, symbol, condition_data):
        condition_data = super().evaluate_complex_symbol(symbol, condition_data)

        if condition_data:
            LinkDatabase.info(
                "Symbol evaluator condition data:{}".format(condition_data)
            )
            return Q(**condition_data)

    def evaluate_simple_symbol(self, symbol):
        result = None
        for item in self.default_search_symbols:
            input_map = {item: symbol}

            if result is None:
                result = Q(**input_map)
            else:
                result |= Q(**input_map)

        return result

    def enhance_condition_data(self, condition_data):
        if condition_data[0].find("__isnull") >= 0:
            condition_data[2] = condition_data[2] == "True"

    def translate_condition(self, condition_data):
        """
        https://docs.djangoproject.com/en/4.2/ref/models/querysets/#field-lookups
        """

        if condition_data[1] == "===":
            return {condition_data[0] + "__iexact": condition_data[2]}
        elif condition_data[1] == ">=":
            return {condition_data[0] + "__gte": condition_data[2]}
        elif condition_data[1] == "<=":
            return {condition_data[0] + "__lte": condition_data[2]}
        elif condition_data[1] == ">":
            return {condition_data[0] + "__gt": condition_data[2]}
        elif condition_data[1] == "<":
            return {condition_data[0] + "__lt": condition_data[2]}
        elif condition_data[1] == "==":
            return {condition_data[0]: condition_data[2]}
        elif condition_data[1] == "=":
            # for title__isnull = True, there are no additions
            if self.is_django_operator(condition_data[0]):
                return {condition_data[0]: condition_data[2]}
            # otherwise translate to contains
            else:
                return {condition_data[0] + "__icontains": condition_data[2]}

        return condition_data

    def is_translatable(self, condition):
        if len(self.translatable_names) == 0:
            return True

        for name in self.translatable_names:
            if condition[0] == name or self.get_django_key(condition[0]) == name:
                return True
        return False

    def get_django_key(self, key):
        wh = key.rfind("__")
        if wh >= 0:
            key_word = key[:wh]
            return key_word
        else:
            return key

    def is_django_operator(self, operator):
        for django_operator in self.django_operators:
            if operator.endswith("__" + django_operator):
                return True

        return False

    def is_archive_source(self):
        return False

    def set_default_search_symbols(self, symbols):
        self.default_search_symbols = symbols


class BaseQueryFilter(object):
    def __init__(self, args, page_limit=False, user=None, init_objects=None):
        self.args = args
        self.use_page_limit = page_limit

        self.user = user
        self.errors = []
        self.init_objects = init_objects
        self.filtered_objects = None

    def get_init_objects(self):
        return self.init_objects

    def set_init_objects(self, init_objects):
        self.init_objects = init_objects

    def get_filtered_objects(self):
        """
        returns filtered objects
        """
        if self.filtered_objects:
            return self.filtered_objects

        self.filtered_objects = self.get_filtered_objects_internal()
        self.filtered_objects = self.filtered_objects.distinct()

        if self.use_page_limit:
            limit_range = self.get_limit()
            if limit_range:
                self.filtered_objects = self.filtered_objects[
                    limit_range[0] : limit_range[1]
                ]

        return self.filtered_objects

    def get_filtered_objects_internal(self):
        conditions = self.get_conditions()
        LinkDatabase.info("Filter conditions: {}".format(conditions))

        objects = self.get_init_objects()

        if conditions is not None:
            return objects.filter(conditions)
        else:
            return objects.none()

    def get_model_pagination(self):
        return 100

    def get_limit(self):
        if "page" in self.args:
            try:
               page = int(self.args["page"])
            except ValueError:
                page = 1
        else:
            page = 1

        paginate_by = self.get_model_pagination()
        # for page 1, paginate_by 100  we have range 0..99
        # for page 2, paginate_by 100  we have range 100..199

        start = (page - 1) * paginate_by

        return [start, start + paginate_by]

    def is_error(self):
        return len(self.errors) > 0

    def get_conditions(self):
        q = Q()

        q1 = self.get_args_filter_query()
        q2 = self.get_omni_query()

        if q1 is None or q2 is None:
            self.errors.append("Both queries are none")

        if q1:
            q &= q1
        if q2:
            q &= q2

        # if q is None or q == Q():
        #    q &= Q(enabled=True)

        return q

    def get_omni_query(self):
        args = self.args.dict()
        args["user"] = self.user

        query_filter = OmniSearchFilter(args)

        translate_names = self.get_translateable_fields()
        query_filter.set_translation_mapping(translate_names)
        query_filter.set_default_search_symbols(self.get_default_omni_search_fields())

        conditions = query_filter.get_conditions()

        not_translateds = query_filter.get_not_translated_conditions()
        if len(not_translateds) > 0:
            for not_translated in not_translateds:
                self.errors.append("Not translated: {}".format(not_translated))

        return conditions

    def get_translateable_fields(self):
        """
        provide which words can be used for filtering in omni search
        """
        return []

    def get_default_omni_search_fields(self):
        """
        If a word is written "omni" search, we want some fields to automatically filter
        """
        return []

    def get_args_filter_query(self):
        """
        returns condition for GET arguments, that should be used to create Q() filter
        """
        args = self.get_args_filter_map()
        return Q(**args)

    def get_args_filter_map(self):
        """
        returns map from GET, for args that should be used to create Q() filter conditions
        """
        parameter_map = {}
        for key in self.args:
            translatables = self.get_translateable_fields()

            wh = key.rfind("__")
            if wh >= 0:
                key_word = key[:wh]
                key_operator = key[wh+2:]

                if key_word in translatables:
                    """ title__icontains """
                    value = self.get_args_filter_map_value(key)
                    if value:
                        parameter_map[key] = value
                elif key in translatables:
                    """ object__foreign__title """
                    value = self.get_args_filter_map_value(key)
                    if value:
                        parameter_map[key] = value
            else:
                if key in translatables:
                    value = self.get_args_filter_map_value(key)
                    if value:
                        parameter_map[key] = value

        return parameter_map

    def get_args_filter_map_value(self, keyword):
        value = self.args.get(keyword)
        if value and value != "":
            return value

    def time_start(self):
        from datetime import datetime

        self.time_start = datetime.now()
        return ""

    def time_stop(self):
        from datetime import datetime

        LinkDatabase.info(
            "Page display time delta:{}".format(datetime.now() - self.time_start)
        )
        return ""


class SourceFilter(BaseQueryFilter):
    def __init__(self, args, user=None, init_objects=None):
        super().__init__(args, user=user, init_objects=init_objects)

    def get_init_objects(self):
        if self.init_objects:
            return self.init_objects

        return SourceDataController.objects

    def get_default_omni_search_fields(self):
        return [
                "title__icontains",
                "url__icontains",
               ]

    def get_translateable_fields(self):
        return SourceDataController.get_query_names()

    def get_model_pagination(self):
        from .viewspkg.sources import SourceListView

        try:
            return int(SourceListView.get_paginate_by())
        except ValueError:
            return 100


class EntryFilter(BaseQueryFilter):
    def __init__(self, args, user=None, use_archive=False):
        super().__init__(args, user=user)
        self.time_limit = None

        self.use_archive_source = use_archive

    def get_model_pagination(self):
        from .viewspkg.entries import EntriesSearchListView

        try:
            return int(EntriesSearchListView.get_paginate_by())
        except ValueError:
            return 100

    def get_init_objects(self):
        if not self.use_archive_source:
            return LinkDataController.objects
        else:
            return ArchiveLinkDataController.objects

    def get_conditions(self):
        q = super().get_conditions()

        q = self.apply_age_limit(q)

        return q

    def apply_age_limit(self, query):
        this_query = None

        if self.user:
            if self.user.is_authenticated:
                uc = UserConfig.get(self.user)
                this_query = Q(age__lt=uc.get_age()) | Q(age=0) | Q(age__isnull=True)
            else:
                this_query = Q(age=0) | Q(age__isnull=True)
        else:
            this_query = Q(age=0) | Q(age__isnull=True)

        if query == Q() and this_query:
            query = this_query
        elif this_query:
            query = query & this_query

        return query

    def get_translateable_fields(self):
        return LinkDataController.get_query_names()

    def get_default_omni_search_fields(self):
        return [
                "title__icontains",
                "link__icontains",
                "description__icontains",
                "tags__tag__icontains",
            ]

    def set_time_limit(self, time_limit):
        self.time_limit = time_limit


class DomainFilter(BaseQueryFilter):
    def __init__(self, args, user=None):
        super().__init__(args, user)

    def get_init_objects(self):
        return DomainsController.objects

    def get_default_omni_search_fields(self):
        return [
                "category__icontains",
                "subcategory__icontains",
                "domain__icontains",
            ]

    def get_translateable_fields(self):
        translate = DomainsController.get_query_names()


class OmniSearchWithDefault(OmniSearch):
    def __init__(self, search_query, evaluator):
        super().__init__(search_query, evaluator)

        self.default_search_symbols = []

    def set_default_search_symbols(self, symbols):
        self.default_search_symbols = symbols
        self.symbol_evaluator.default_search_symbols = symbols

    def get_combined_query(self):
        """
        To speed things up, if query does not have any operator, use default scheme for searching
        """
        query = Q()

        if self.is_complex_query():
            query = super().get_combined_query()
        else:
            query = self.get_combined_query_simple()

        if query is None:
            self.errors.append("Query is none")
            query = Q()

        return query

    def get_combined_query_simple(self):
        symbol = self.search_query

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


class OmniSearchFilter(BaseQueryFilter):
    def __init__(self, args, init_objects = None):
        super().__init__(args, init_objects = init_objects)

        self.search_query = get_search_term(args)
        if not self.search_query:
            self.search_query = ""

        self.parser = OmniSearchWithDefault(
            self.search_query, DjangoSingleSymbolEvaluator()
        )

        self.query_set = None
        self.combined_query = None

    def set_default_search_symbols(self, symbols):
        self.parser.set_default_search_symbols(symbols)

    def set_translation_mapping(self, name_mapping):
        self.parser.set_translation_mapping(name_mapping)

    def get_conditions(self):
        if self.combined_query:
            return self.combined_query

        self.combined_query = self.parser.get_query_result()
        self.errors.extend(self.parser.errors)

        return self.combined_query

    def get_translated_conditions(self):
        return self.parser.get_translated_conditions()

    def get_not_translated_conditions(self):
        return self.parser.get_not_translated_conditions()
