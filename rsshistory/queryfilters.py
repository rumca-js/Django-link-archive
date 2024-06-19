from django.db.models import Q
from django.utils.http import urlencode

from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    DomainsController,
)
from .apps import LinkDatabase
from .models import UserConfig, AppLogging

from .omnisearch import SingleSymbolEvaluator, OmniSearch


class BaseQueryFilter(object):
    def __init__(self, args, page_limit=False, user=None):
        self.args = args
        self.use_page_limit = page_limit

        if "archive" in self.args and self.args["archive"] == "on":
            self.use_archive_source = True
        else:
            self.use_archive_source = False

        self.user = user
        self.error = False
        self.filtered_objects = None

    def get_conditions(self):
        return Q()

    def get_objects(self):
        return None

    def get_filtered_objects(self):
        if self.filtered_objects:
            return self.filtered_objects

        """
        This needs to be here for JSON only.
        TODO rewrite this. JSON should use pagination on filtered objects
        """
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

        objects = self.get_objects()

        if conditions is not None:
            return objects.filter(conditions)
        else:
            return objects.none()

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

    def is_error(self):
        return self.error

    def get_filter_args_map(self):
        parameter_map = {}
        for key in self.get_filter_args_map_keys():
            value = self.get_filter_args_value(key)
            if value:
                parameter_map[key] = value

        return parameter_map

    def get_filter_args_map_keys(self):
        return []

    def get_filter_args_value(self, keyword):
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
    def __init__(self, args, user=None):
        super().__init__(args, user=user)

    def get_objects(self):
        return SourceDataController.objects

    def get_conditions(self):
        q = Q()

        q1 = self.get_arg_conditions_query()
        q2 = self.get_omni_conditions()

        if q1 is None or q2 is None:
            self.error = True

        if q1:
            q &= q1
        if q2:
            q &= q2

        if q is None or q == Q():
            q &= Q(enabled=True)

        return q

    def get_omni_conditions(self):
        args = self.args.dict()
        args["user"] = self.user

        query_filter = OmniSearchFilter(args)

        translate = SourceDataController.get_query_names()
        query_filter.set_translation_mapping(translate)

        query_filter.set_default_search_symbols(
            [
                "title__icontains",
                "url__icontains",
            ]
        )

        query_filter.get_conditions()
        return query_filter.combined_query

    def get_arg_conditions_query(self):
        args = self.get_filter_args_map()
        return Q(**args)

    def get_filter_args_map_keys(self):
        return ["category", "subcategory", "title", "url"]

    def get_model_pagination(self):
        from .viewspkg.viewsources import SourceListView

        return int(SourceListView.paginate_by)


class EntryFilter(BaseQueryFilter):
    def __init__(self, args, user=None):
        super().__init__(args, user=user)
        self.time_limit = None

        self.use_archive_source = False
        self.additional_condition = Q()

    def get_model_pagination(self):
        from .viewspkg.viewentries import EntriesSearchListView

        return int(EntriesSearchListView.paginate_by)

    def get_objects(self):
        if not self.use_archive_source:
            return LinkDataController.objects
        else:
            return ArchiveLinkDataController.objects

    def get_conditions(self):
        q = Q()

        q1 = self.get_arg_conditions_query()
        q2 = self.get_omni_conditions()
        q3 = self.additional_condition

        if q1 is None or q2 is None:
            self.error = True

        if q1:
            q &= q1
        if q2:
            q &= q2
        if q3:
            q &= q3

        q = self.apply_age_limit(q)

        # AppLogging.info("part query: {}".format(q1, q2, q3))
        # AppLogging.info("query: {}".format(q))

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

    def get_omni_conditions(self):
        args = self.args.dict()
        args["user"] = self.user

        query_filter = OmniSearchFilter(args)

        translate = LinkDataController.get_query_names()
        query_filter.set_translation_mapping(translate)

        query_filter.set_default_search_symbols(
            [
                "title__icontains",
                "link__icontains",
                "description__icontains",
                "tags__tag__icontains",
            ]
        )

        query_filter.get_conditions()
        return query_filter.combined_query

    def get_arg_conditions_query(self):
        args = self.get_arg_conditions(True)
        return Q(**args)

    def get_sources(self):
        self.sources = None

    def set_time_limit(self, time_limit):
        self.time_limit = time_limit

    def set_archive_source(self, source):
        self.use_archive_source = source

    def set_additional_condition(self, condition):
        self.additional_condition = condition

    def get_hard_query_limit(self):
        10000

    def get_filter_args_map_keys(self):
        return [
            "title",
            "description",
            "thumbnail",
            "language",
            "age",
            "date_from",
            "date_to",
            "permanent",
            "bookmarked",
            "dead",
            "user",
            "tag",
            "artist",
            "album",
            "vote",
            # not related to entry/link
            "source_id",
            "source_title",
            "category",
            "subcategory",
            "archive",
        ]

    def get_arg_conditions(self, translate=False):
        parameter_map = {}
        # TODO change to new API get_filter_args_map

        if not translate:
            return self.get_filter_args_map()
        else:
            self.copy_if_is_set_and_translate(parameter_map, self.args, "title")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "language")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "user")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "tag")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "vote")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "source_id")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "source_title")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "permanent")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "bookmarked")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "category")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "subcategory")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "artist")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "album")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "date_from")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "date_to")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "age")

            if self.time_limit:
                if "date_published__range" not in parameter_map:
                    date_range = self.time_limit
                    parameter_map["date_published__range"] = [
                        date_range[0],
                        date_range[1],
                    ]

        return parameter_map

    def copy_if_is_set_and_translate(self, dst, src, element):
        mapping = self.get_arg_title_translation()

        if element in src and src[element] != "":
            if element in mapping:
                # simple translate
                dst[mapping[element]] = src[element]

            # special processing
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
            else:
                dst[element] = src[element]

    def get_arg_title_translation(self):
        return {
            "title": "title__icontains",
            "language": "language__icontains",
            "category": "source_obj__category",
            "subcategory": "source_obj__subcategory",
            "source_id": "source_obj__id",
            "source_title": "source_obj__title",
            "user": "user__icontains",
            "vote": "votes__vote__gt",
            "artist": "artist__icontains",
            "album": "album__icontains",
        }


class DomainFilter(BaseQueryFilter):
    def __init__(self, args, user=None):
        super().__init__(args, user)

    def get_objects(self):
        return DomainsController.objects

    def get_conditions(self):
        q = Q()

        q1 = self.get_arg_conditions_query()
        q2 = self.get_omni_conditions()

        if q1 is None or q2 is None:
            self.error = True

        if q1:
            q &= q1
        if q2:
            q &= q2

        return q

    def get_omni_conditions(self):
        args = self.args.dict()
        args["user"] = self.user

        query_filter = OmniSearchFilter(args)

        translate = DomainsController.get_query_names()
        query_filter.set_translation_mapping(translate)

        query_filter.set_default_search_symbols(
            [
                "category__icontains",
                "subcategory__icontains",
                # TODO re-enable some day "link_obj__title__icontains",
                "domain__icontains",
                # "link_obj__description__icontains",
            ]
        )

        query_filter.get_conditions()
        return query_filter.combined_query

    def get_arg_conditions_query(self):
        args = self.get_filter_args_map()
        return Q(**args)

    def get_filter_args_map_keys(self):
        return ["suffix", "tld", "main", "domain", "category", "subcategory"]


class DjangoSingleSymbolEvaluator(SingleSymbolEvaluator):
    def __init__(self):
        super().__init__()
        self.default_search_symbols = []

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

        if condition_data[1] == "==":
            return {condition_data[0] + "__iexact": condition_data[2]}
        elif condition_data[1] == ">=":
            return {condition_data[0] + "__gte": condition_data[2]}
        elif condition_data[1] == "<=":
            return {condition_data[0] + "__lte": condition_data[2]}
        elif condition_data[1] == ">":
            return {condition_data[0] + "__gt": condition_data[2]}
        elif condition_data[1] == "<":
            return {condition_data[0] + "__lt": condition_data[2]}
        elif condition_data[1] == "?=":
            return {condition_data[0]: condition_data[2]}
        elif condition_data[1] == "=":
            # for title__isnull = True, there are no additions
            if self.is_django_operator(condition_data[0]):
                return {condition_data[0]: condition_data[2]}
            # otherwise translate to contains
            else:
                return {condition_data[0] + "__icontains": condition_data[2]}

    def is_django_operator(self, operator):
        return (
            operator.endswith("__isnull")
            or operator.endswith("__iexact")
            or operator.endswith("__gte")
            or operator.endswith("__lte")
            or operator.endswith("__gt")
            or operator.endswith("__lt")
            or operator.endswith("__range")
        )

    def is_archive_source(self):
        return False

    def set_default_search_symbols(self, symbols):
        self.default_search_symbols = symbols


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
            self.error = True
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
    def __init__(self, args):
        super().__init__(args)

        if "search_history" in self.args and self.args["search_history"] != "":
            self.search_query = self.args["search_history"]
        elif "search" in self.args and self.args["search"] != "":
            self.search_query = self.args["search"]
        else:
            self.search_query = ""

        self.parser = OmniSearchWithDefault(
            self.search_query, DjangoSingleSymbolEvaluator()
        )

        self.query_set = None
        self.combined_query = None

    def set_query_set(self, query_set):
        self.query_set = query_set

    def set_default_search_symbols(self, symbols):
        self.parser.set_default_search_symbols(symbols)

    def set_translation_mapping(self, name_mapping):
        self.parser.set_translation_mapping(name_mapping)

    def get_conditions(self):
        if self.combined_query:
            return self.combined_query

        self.combined_query = self.parser.get_query_result()
        return self.combined_query

    def get_objects(self):
        return self.query_set

    def get_translated_conditions(self):
        return self.parser.get_translated_conditions()

    def get_not_translated_conditions(self):
        return self.parser.get_not_translated_conditions()
