from datetime import datetime, timedelta, date
from django import forms

from .models import (
    LinkTagsDataModel,
    LinkCommentDataModel,
    LinkVoteDataModel,
)
from .models import ConfigurationEntry, UserConfig
from .controllers import SourceDataController, LinkDataController


# https://docs.djangoproject.com/en/4.1/ref/forms/widgets/


def my_date_to():
    from .dateutils import DateUtils

    return DateUtils.get_days_range()[1]


def my_date_from():
    from .dateutils import DateUtils

    return DateUtils.get_days_range()[0]




class ConfigForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = ConfigurationEntry
        fields = [
            "data_export_path",
            "data_import_path",
            "link_archive",
            "source_archive",
            "sources_refresh_period",
            "git_path",
            "git_repo",
            "git_daily_repo",
            "git_user",
            "git_token",
        ]
        widgets = {}

    def __init__(self, *args, **kwargs):
        super(ConfigForm, self).__init__(*args, **kwargs)
        self.fields["git_path"].required = False
        self.fields["git_repo"].required = False
        self.fields["git_daily_repo"].required = False
        self.fields["git_user"].required = False
        self.fields["git_token"].required = False


class UserConfigForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = UserConfig
        fields = ["show_icons", "thumbnails_as_icons", "small_icons", "display_type"]
        # fields = ['show_icons', 'thumbnails_as_icons', 'small_icons', 'display_type', 'theme', 'links_per_page']
        # widgets = {
        # }


class ImportSourceRangeFromInternetArchiveForm(forms.Form):
    source_url = forms.CharField(label="Source url", max_length=500)
    archive_start = forms.DateField(label="Start time")
    archive_stop = forms.DateField(label="Stop time")


class ExportDailyDataForm(forms.Form):
    time_start = forms.DateField(label="Start time")
    time_stop = forms.DateField(label="Stop time")


class PushDailyDataForm(forms.Form):
    input_date = forms.DateField(label="Input date", initial=my_date_from)


class LinkInputForm(forms.Form):
    link = forms.CharField(label="Link", max_length=500)

    def get_information(self):
        return self.cleaned_data


class SourceInputForm(forms.Form):
    url = forms.CharField(label="Source URL", max_length=500)

    def get_information(self):
        return self.cleaned_data


class ExportTopicForm(forms.Form):
    tag = forms.CharField(label="Tag", max_length=500)


class YouTubeLinkSimpleForm(forms.Form):
    """
    Import links form
    """

    youtube_link = forms.CharField(label="YouTube Link URL", max_length=500)


class OmniSearchForm(forms.Form):
    """
    Import links form
    """

    search = forms.CharField(label="Search for", max_length=500)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["search"].widget.attrs.update(size="100")


class Conditions(object):
    def __init__(self, data):
        self.data = data

    def is_data(self):
        return len(self.data) > 0

    def is_operator(self):
        return self.data[0] in ("(", ")", "=", "!", "<", ">", "=", "&", "|", "^")

    def get_operator(self):
        return self.data

    def is_condition(self):
        return not self.is_operator()

    def add(self, newchar):
        self.data += str(newchar)

    def ready(self):
        self.data = self.data.strip()

    def str(self):
        return self.data

    def __str__(self):
        return self.data


from django.db.models import Q


class OmniSearchProcessor(object):
    def __init__(self, data):
        self.data = data
        self.conditions = []

    def is_operator(self, char):
        return char in ("(", ")", "=", "!", "<", ">", "&", "|", "^")

    def is_condition(self, char):
        return not self.is_operator(char)

    def parse_conditions(self):
        conditions = []
        bracket_count = 0
        current_condition = Conditions("")

        for char in self.data:
            if char == "(":
                bracket_count += 1
            elif char == ")":
                bracket_count -= 1

            if current_condition.is_data():
                if self.is_operator(char) and current_condition.is_operator():
                    current_condition.add(char)
                elif self.is_condition(char) and current_condition.is_condition():
                    current_condition.add(char)
                else:
                    current_condition.ready()
                    conditions.append(current_condition)
                    current_condition = Conditions(char)
            else:
                current_condition.add(char)

        if current_condition.is_data():
            current_condition.ready()
            conditions.append(current_condition)

        return conditions

    def get_eval_query(self, celem):
        c0 = celem[0].data
        c1 = celem[1].data
        c2 = celem[2].data

        if c1 == "==":
            return {c0 + "__exact": c2}
        if c1 == "=":
            return {c0 + "__contains": c2}
        else:
            return {c0: c2}

    def filter_queryset(self, queryset):
        conditions = self.parse_conditions()

        combined_q_object = None

        for key in range(int((len(conditions) + 1) / 4)):
            if key == 0:
                condition_text = self.get_eval_query(conditions[key * 4 : key * 4 + 3])
                if combined_q_object is None:
                    combined_q_object = Q(**condition_text)
            else:
                condition = conditions[key * 4 - 1]
                if condition.get_operator() == "&":
                    condition_text = self.get_eval_query(
                        conditions[key * 4 : key * 4 + 3]
                    )
                    combined_q_object &= Q(**condition_text)
                if condition.get_operator() == "|":
                    condition_text = self.get_eval_query(
                        conditions[key * 4 : key * 4 + 3]
                    )
                    combined_q_object |= Q(**condition_text)

        filtered_queryset = queryset.filter(combined_q_object)
        print("Omni query:{}".format(filtered_queryset.query))
        return filtered_queryset


class EntryForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = LinkDataController
        fields = [
            "link",
            "title",
            "description",
            "date_published",
            "source",
            "persistent",
            "language",
            "user",
            "artist",
            "album",
            "thumbnail",
        ]

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields["link"].required = True
        self.fields["source"].required = False
        self.fields["language"].required = False
        self.fields["description"].required = False
        self.fields["title"].required = False
        self.fields["artist"].required = False
        self.fields["album"].required = False
        self.fields["persistent"].initial = True
        self.fields["user"].widget.attrs["readonly"] = True
        self.fields["thumbnail"].required = False

    def get_information(self):
        return self.cleaned_data

    def save_form(self, data):
        source = data["source"]
        title = data["title"]
        description = data["description"]
        link = data["link"]
        date_published = data["date_published"]
        persistent = data["persistent"]
        language = data["language"]
        user = data["user"]
        thumbnail = data["thumbnail"]
        artist = data["artist"]
        album = data["album"]

        if not title or not source:
            return False

        source_obj = None
        sources = SourceDataController.objects.filter(url=source)
        if sources.exists():
            source_obj = sources[0]

        links = LinkDataController.objects.filter(link=link)
        if len(links) > 0:
            return False

        entry = LinkDataController(
            source=source,
            title=title,
            description=description,
            link=link,
            date_published=date_published,
            persistent=persistent,
            thumbnail=thumbnail,
            language=language,
            user=user,
            artist=artist,
            album=album,
            source_obj=source_obj,
        )

        entry.save()
        return True


class SourceForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = SourceDataController
        fields = [
            "url",
            "title",
            "source_type",
            "category",
            "subcategory",
            "language",
            "fetch_period",
            "export_to_cms",
            "remove_after_days",
            "favicon",
            "on_hold",
        ]
        widgets = {}

    def __init__(self, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)
        self.fields["favicon"].required = False


class TagEntryForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = LinkTagsDataModel
        fields = ["link", "author", "date", "tag"]
        widgets = {}

    def save_tags(self):
        link = self.cleaned_data["link"]
        author = self.cleaned_data["author"]
        date = self.cleaned_data["date"]
        tags = self.cleaned_data["tag"]

        objs = LinkTagsDataModel.objects.filter(author=author, link=link)
        if objs.exists():
            objs.delete()

        tags_set = set()
        tags = tags.split(LinkTagsDataModel.get_delim())
        for tag in tags:
            tag = str(tag).strip()
            tag = tag.lower()
            if tag != "":
                tags_set.add(tag)

        link_objs = LinkDataController.objects.filter(link=link)

        for tag in tags_set:
            model = LinkTagsDataModel(
                link=link, author=author, date=date, tag=tag, link_obj=link_objs[0]
            )
            model.save()


class TagRenameForm(forms.Form):
    """
    Category choice form
    """

    current_tag = forms.CharField(label="Current tag", max_length=100)
    new_tag = forms.CharField(label="New tag", max_length=100)


class SourcesChoiceForm(forms.Form):
    """
    Category choice form
    """

    category = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory = forms.CharField(widget=forms.Select(choices=()), required=False)
    title = forms.CharField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
        self.args = kwargs.pop("args", ())
        super().__init__(*args, **kwargs)

    def create(self, filtered_objects):
        self.filtered_objects = filtered_objects

        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        categories = self.get_filtered_objects_values("category")
        subcategories = self.get_filtered_objects_values("subcategory")
        title = self.get_filtered_objects_values("title")

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        self.fields["category"].widget = forms.Select(choices=categories, attrs=attr)
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )
        self.fields["title"].widget = forms.Select(choices=title, attrs=attr)

    def get_filtered_objects_values(self, field):
        values = set()
        values.add("Any")

        for val in self.filtered_objects.values(field):
            if str(val).strip() != "":
                values.add(val[field])

        dict_values = self.to_dict(values)

        return dict_values

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
            if item.strip() != "":
                if item == "Any":
                    result.append(("", item))
                else:
                    result.append((item, item))
        return result


class SourceChoiceArgsExtractor(object):
    def __init__(self, args):
        self.args = args

    def get_filtered_objects(self, input_query=None):
        parameter_map = self.get_filter_args()

        if input_query is None:
            self.filtered_objects = SourceDataController.objects.filter(**parameter_map)
        else:
            self.filtered_objects = SourceDataController.objects.filter(
                Q(**parameter_map) & input_query
            )
        return self.filtered_objects

    def get_filter_args(self):
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

    def get_filter_string(self):
        infilters = self.get_filter_args()

        filter_string = ""
        for key in infilters:
            filter_string += "&{0}={1}".format(key, infilters[key])

        # TODO try urlencode
        return filter_string


class BasicEntryChoiceForm(forms.Form):
    category = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory = forms.CharField(widget=forms.Select(choices=()), required=False)
    source_title = forms.CharField(widget=forms.Select(choices=()), required=False)

    def create(self, sources):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        self.sources = sources

        categories = self.get_filtered_objects_values("category")
        subcategories = self.get_filtered_objects_values("subcategory")
        title = self.get_filtered_objects_values("title")

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        self.fields["category"].widget = forms.Select(choices=categories, attrs=attr)
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )
        self.fields["source_title"].widget = forms.Select(choices=title, attrs=attr)

    def get_filtered_objects_values(self, field):
        values = set()
        values.add("Any")

        if len(self.sources) > 0:
            for val in self.sources.values(field):
                if str(val).strip() != "":
                    values.add(val[field])

        dict_values = self.to_dict(values)

        return dict_values

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
            if item.strip() != "":
                if item == "Any":
                    result.append(("", item))
                else:
                    result.append((item, item))
        return result


class EntryBookmarksChoiceForm(BasicEntryChoiceForm):
    """
    Category choice form
    """

    # do not think too much about these settings, these will be overriden by 'create' method
    title = forms.CharField(label="title", max_length=1000, required=False)
    tag = forms.CharField(label="tag", max_length=500, required=False)
    vote = forms.IntegerField(label="vote", required=False)


class EntryChoiceForm(BasicEntryChoiceForm):
    """
    Category choice form
    """

    # do not think too much about these settings, these will be overriden by 'create' method
    title = forms.CharField(label="title", max_length=1000, required=False)
    persistent = forms.BooleanField(required=False, initial=False)
    language = forms.CharField(label="language", max_length=10, required=False)
    user = forms.CharField(label="user", max_length=500, required=False)
    tag = forms.CharField(label="tag", max_length=500, required=False)
    vote = forms.IntegerField(label="vote", required=False)
    artist = forms.CharField(label="artist", max_length=1000, required=False)
    album = forms.CharField(label="album", max_length=1000, required=False)
    date_to = forms.DateField(required=False, initial=my_date_to)
    date_from = forms.DateField(required=False, initial=my_date_from)
    archive = forms.BooleanField(required=False, initial=False)


class EntryChoiceArgsExtractor(object):
    def __init__(self, args):
        self.args = args
        self.time_constrained = True
        if "archive" in self.args and self.args["archive"] == "on":
            self.archive_source = True
        else:
            self.archive_source = False

    def get_sources(self):
        self.sources = SourceDataController.objects.all()

    def set_time_constrained(self, constrained):
        self.time_constrained = constrained

    def set_archive_source(self, source):
        self.archive_source = source

    def get_filtered_objects(self, input_query=None):
        source_parameter_map = self.get_source_filter_args(False)
        entry_parameter_map = self.get_entry_filter_args(False)

        print("Entry parameter map: {}".format(str(entry_parameter_map)))

        if input_query == None:
            if not self.archive_source:
                self.entries = LinkDataController.objects.filter(**entry_parameter_map)
            if self.archive_source:
                from .controllers import ArchiveLinkDataController

                self.entries = ArchiveLinkDataController.objects.filter(
                    **entry_parameter_map
                    )[:self.get_hard_query_limit()]
        else:
            if not self.archive_source:
                self.entries = LinkDataController.objects.filter(
                    Q(**entry_parameter_map) & input_query
                )
            if self.archive_source:
                from .models import ArchiveLinkDataModel

                self.entries = ArchiveLinkDataModel.objects.filter(
                    Q(**entry_parameter_map) & input_query
                    )[:self.get_hard_query_limit()]

        return self.entries

    def get_hard_query_limit(self):
        10000

    def get_source_filter_args(self, pure_data=True):
        parameter_map = {}

        category = self.args.get("category")
        if category and category != "Any":
            parameter_map["category"] = category

        subcategory = self.args.get("subcategory")
        if subcategory and subcategory != "Any":
            parameter_map["subcategory"] = subcategory

        if pure_data:
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

    def get_entry_filter_args(self, pure_data=True):
        parameter_map = {}

        if pure_data:
            self.copy_if_is_set(parameter_map, self.args, "title")
            self.copy_if_is_set(parameter_map, self.args, "language")
            self.copy_if_is_set(parameter_map, self.args, "user")
            self.copy_if_is_set(parameter_map, self.args, "tag")
            self.copy_if_is_set(parameter_map, self.args, "vote")
            self.copy_if_is_set(parameter_map, self.args, "category")
            self.copy_if_is_set(parameter_map, self.args, "subcategory")
            self.copy_if_is_set(parameter_map, self.args, "source_title")
            self.copy_if_is_set(parameter_map, self.args, "persistent")
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
            self.copy_if_is_set_and_translate(parameter_map, self.args, "category")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "subcategory")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "source_title")
            self.copy_if_is_set_and_translate(parameter_map, self.args, "persistent")
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

    def get_filter_string(self):
        infilters = self.get_source_filter_args()
        infilters.update(self.get_entry_filter_args())

        filter_string = ""
        for key in infilters:
            filter_string += "&{0}={1}".format(key, infilters[key])

        # TODO try urlencode
        return filter_string


class CommentEntryForm(forms.Form):
    """
    Category choice form
    Using forms not model forms, because we would have to passe link somehow
    """

    link_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    author = forms.CharField(max_length=1000)
    comment = forms.CharField(widget=forms.Textarea)
    date_published = forms.DateTimeField(initial=datetime.now)

    def __init__(self, *args, **kwargs):
        super(CommentEntryForm, self).__init__(*args, **kwargs)
        self.fields["author"].readonly = True

    def save_comment(self):
        entry = LinkDataController.objects.get(id=self.cleaned_data["link_id"])

        LinkCommentDataModel.objects.create(
            author=self.cleaned_data["author"],
            comment=self.cleaned_data["comment"],
            date_published=self.cleaned_data["date_published"],
            link_obj=entry,
        )


class LinkVoteForm(forms.Form):
    """
    Category choice form
    """

    link_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    author = forms.CharField(max_length=1000)
    vote = forms.IntegerField(initial=0)

    def __init__(self, *args, **kwargs):
        super(LinkVoteForm, self).__init__(*args, **kwargs)
        self.fields["author"].readonly = True

    def save_vote(self):
        entry = LinkDataController.objects.get(id=self.cleaned_data["link_id"])

        vote = LinkVoteDataModel.objects.filter(
            author=self.cleaned_data["author"], link_obj=entry
        )
        vote.delete()

        LinkVoteDataModel.objects.create(
            author=self.cleaned_data["author"],
            vote=self.cleaned_data["vote"],
            link_obj=entry,
        )
