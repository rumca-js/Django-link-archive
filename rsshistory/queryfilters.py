from django.db.models import Q

from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
)
from .models import Domains


class BaseQueryFilter(object):
    def __init__(self, args):
        self.args = args

    def get_filter_string(self):
        infilters = self.args

        filter_string = ""
        for key in infilters:
            if key != "page" and infilters[key] != "":
                filter_string += "&{0}={1}".format(key, infilters[key])

        # TODO try urlencode
        return filter_string

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


class SourceFilter(BaseQueryFilter):
    def __init__(self, args):
        super().__init__(args)
        self.use_page_limit = False

    def get_filtered_objects(self, input_query=None):
        parameter_map = self.get_filter_args()

        if input_query is None:
            self.filtered_objects = SourceDataController.objects.filter(**parameter_map)
        else:
            self.filtered_objects = SourceDataController.objects.filter(
                Q(**parameter_map) & input_query
            )

        if self.use_page_limit:
            limit_range = self.get_limit()
            if limit_range:
                self.filtered_objects = self.filtered_objects[
                    limit_range[0] : limit_range[1]
                ]

        return self.filtered_objects

    def get_filter_args(self, translate=False):
        parameter_map = {}

        category = self.args.get("category")
        if category and category != "Any":
            parameter_map["category"] = category

        subcategory = self.args.get("subcategory")
        if subcategory and subcategory != "Any":
            parameter_map["subcategory"] = subcategory

        title = self.args.get("title")
        if title and title != "Any":
            parameter_map["title"] = title

        return parameter_map

    def get_model_pagination(self):
        from .viewspkg.viewsources import RssSourceListView
        return int(RssSourceListView.paginate_by)


class EntryFilter(BaseQueryFilter):
    def __init__(self, args):
        super().__init__(args)
        self.time_constrained = True
        self.use_page_limit = False
        if "archive" in self.args and self.args["archive"] == "on":
            self.archive_source = True
        else:
            self.archive_source = False

    def get_model_pagination(self):

        from .viewspkg.viewentries import EntriesSearchListView
        return int(EntriesSearchListView.paginate_by)

    def get_sources(self):
        self.sources = SourceDataController.objects.all()

    def set_time_constrained(self, constrained):
        self.time_constrained = constrained

    def set_archive_source(self, source):
        self.archive_source = source

    def get_filtered_objects(self, input_query=None):
        source_parameter_map = self.get_source_filter_args(True)
        entry_parameter_map = self.get_entry_filter_args(True)

        print("Entry parameter map: {}".format(str(entry_parameter_map)))

        if input_query == None:
            if not self.archive_source:
                self.entries = LinkDataController.objects.filter(**entry_parameter_map)
            if self.archive_source:
                self.entries = ArchiveLinkDataController.objects.filter(
                    **entry_parameter_map
                )
        else:
            if not self.archive_source:
                self.entries = LinkDataController.objects.filter(
                    Q(**entry_parameter_map) & input_query
                )
            if self.archive_source:
                self.entries = ArchiveLinkDataController.objects.filter(
                    Q(**entry_parameter_map) & input_query
                )

        if self.use_page_limit:
            limit_range = self.get_limit()
            if limit_range:
                self.entries = self.entries[limit_range[0] : limit_range[1]]

        return self.entries

    def get_hard_query_limit(self):
        10000

    def get_source_filter_args(self, translate=False):
        parameter_map = {}

        category = self.args.get("category")
        if category and category != "Any":
            parameter_map["category"] = category

        subcategory = self.args.get("subcategory")
        if subcategory and subcategory != "Any":
            parameter_map["subcategory"] = subcategory

        if not translate:
            title = self.args.get("source_title")
            if title and title != "Any":
                parameter_map["source_title"] = title
        else:
            title = self.args.get("source_title")
            if title and title != "Any":
                parameter_map["title"] = title

        return parameter_map

    def get_default_range(self):
        from .dateutils import DateUtils

        return DateUtils.get_days_range()

    def copy_if_is_set(self, dst, src, element):
        if element in src and src[element] != "":
            dst[element] = src[element]

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
            elif element == "persistent":
                if src[element] == "on":
                    dst["persistent"] = True
                else:
                    dst["persistent"] = False
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

    def get_entry_filter_args(self, translate=False):
        parameter_map = {}

        if not translate:
            self.copy_if_is_set(parameter_map, self.args, "title")
            self.copy_if_is_set(parameter_map, self.args, "language")
            self.copy_if_is_set(parameter_map, self.args, "user")
            self.copy_if_is_set(parameter_map, self.args, "tag")
            self.copy_if_is_set(parameter_map, self.args, "vote")
            self.copy_if_is_set(parameter_map, self.args, "source_title")
            self.copy_if_is_set(parameter_map, self.args, "persistent")
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
            self.copy_if_is_set_and_translate(parameter_map, self.args, "persistent")
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

    def get_tag_search(self):
        # TODO remove
        tag = self.args.get("tag")
        if tag is None:
            return None, None

        tag_find_exact, tag = self.get_search_keyword(tag)
        if tag_find_exact:
            key = "tags__tag"
        else:
            key = "tags__tag__icontains"
        return key, tag

    def get_search_keyword(self, text):
        exact_find = False
        if text.find('"') >= 0:
            text = text[1:-1]
            exact_find = True
        return exact_find, text


class DomainFilter(BaseQueryFilter):
    def __init__(self, args):
        super().__init__(args)
        self.use_page_limit = False

    def get_filtered_objects(self, input_query=None):
        parameter_map = self.get_filter_args()

        if input_query is None:
            self.filtered_objects = Domains.objects.filter(**parameter_map)
        else:
            self.filtered_objects = Domains.objects.filter(
                Q(**parameter_map) & input_query
            )

        if self.use_page_limit:
            limit_range = self.get_limit()
            if limit_range:
                self.filtered_objects = self.filtered_objects[
                    limit_range[0] : limit_range[1]
                ]

        return self.filtered_objects

    def get_filter_args(self, translate=False):
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
