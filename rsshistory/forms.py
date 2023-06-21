from datetime import datetime, timedelta
from django import forms

from .models import (
    SourceDataModel,
    LinkDataModel,
    LinkTagsDataModel,
    LinkCommentDataModel,
)
from .models import ConfigurationEntry, UserConfig


# https://docs.djangoproject.com/en/4.1/ref/forms/widgets/


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


class ImportSourceFromInternetArchiveForm(forms.Form):
    source_url = forms.CharField(label="Source url", max_length=500)
    archive_time = forms.DateField(label="Archive time")


class ImportSourceRangeFromInternetArchiveForm(forms.Form):
    source_url = forms.CharField(label="Source url", max_length=500)
    archive_start = forms.DateField(label="Start time")
    archive_stop = forms.DateField(label="Stop time")


class ExportDailyDataForm(forms.Form):
    time_start = forms.DateField(label="Start time")
    time_stop = forms.DateField(label="Stop time")


class ExportTopicForm(forms.Form):
    tag = forms.CharField(label="Tag", max_length=500)


class YouTubeLinkSimpleForm(forms.Form):
    """
    Import links form
    """

    youtube_link = forms.CharField(label="YouTube Link URL", max_length=500)


class SourceForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = SourceDataModel
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
        widgets = {
            # 'git_token': forms.PasswordInput(),
        }

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
        widgets = {
            # 'git_token': forms.PasswordInput(),
        }

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

        link_objs = LinkDataModel.objects.filter(link=link)

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


class ImportSourcesForm(forms.Form):
    """
    Import links form
    """

    rawsources = forms.CharField(
        widget=forms.Textarea(attrs={"name": "rawsources", "rows": 30, "cols": 100})
    )

    def get_sources(self):
        from .serializers.converters import CsvConverter

        rawsources = self.cleaned_data["rawsources"]

        converter = CsvConverter()
        return converter.from_text(rawsources)


class ImportEntriesForm(forms.Form):
    """
    Import links form
    """

    rawentries = forms.CharField(
        widget=forms.Textarea(attrs={"name": "rawentries", "rows": 30, "cols": 100})
    )

    def get_entries(self):
        from .serializers.converters import CsvConverter

        rawentries = self.cleaned_data["rawentries"]

        converter = CsvConverter()
        return converter.from_text(rawsources)


class EntryForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = LinkDataModel
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
        ]
        # widgets = {
        # #'git_token': forms.PasswordInput(),
        # }

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

    def get_information(self):
        return self.cleaned_data

    def get_full_information(self):
        data = self.get_information()
        return self.update_info(data)

    def update_info(self, data):
        from .webtools import Page

        p = Page(data["link"])

        data["thumbnail"] = None

        if p.is_youtube():
            self.update_info_youtube(data)

        return self.update_info_default(data)

    def update_info_youtube(self, data):
        from .pluginentries.youtubelinkhandler import YouTubeLinkHandler

        h = YouTubeLinkHandler(data["link"])
        h.download_details()

        data["source"] = h.get_channel_feed_url()
        data["link"] = h.get_link_url()
        data["title"] = h.get_title()
        data["description"] = h.get_description()
        data["date_published"] = h.get_datetime_published()
        data["thumbnail"] = h.get_thumbnail()

        return data

    def update_info_default(self, data):
        from .webtools import Page

        p = Page(data["link"])
        if not data["source"]:
            data["source"] = p.get_domain()
        if not data["language"]:
            data["language"] = p.get_language()
        if not data["title"]:
            data["title"] = p.get_title()
        if not data["description"]:
            data["description"] = p.get_title()
        return data

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

        if not title or not source:
            return False

        source_obj = None
        sources = SourceDataModel.objects.filter(url=source)
        if sources.exists():
            source_obj = sources[0]

        links = LinkDataModel.objects.filter(link=link)
        if len(links) > 0:
            return False

        entry = LinkDataModel(
            source=source,
            title=title,
            description=description,
            link=link,
            date_published=date_published,
            persistent=persistent,
            thumbnail=thumbnail,
            language=language,
            user=user,
            source_obj=source_obj,
        )

        entry.save()
        return True


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

    def get_filtered_objects(self):
        parameter_map = self.get_filter_args()
        self.filtered_objects = SourceDataModel.objects.filter(**parameter_map)
        return self.filtered_objects

    def create(self):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        categories = self.get_filtered_objects_values("category")
        subcategories = self.get_filtered_objects_values("subcategory")
        title = self.get_filtered_objects_values("title")

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        # default form value
        # https://stackoverflow.com/questions/604266/django-set-default-form-values
        category_init = self.get_init("category")
        subcategory_init = self.get_init("subcategory")
        title_init = self.get_init("title")

        self.fields["category"].widget = forms.Select(choices=categories, attrs=attr)
        self.fields["category"].initial = category_init
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )
        self.fields["subcategory"].initial = subcategory_init
        self.fields["title"].initial = title_init

    def get_init(self, column):
        filters = self.get_filter_args()
        if column in filters:
            return filters[column]
        else:
            return ""

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


class EntryChoiceForm(forms.Form):
    """
    Category choice form
    """

    # do not think too much about these settings, these will be overriden by 'create' method
    search = forms.CharField(label="Search", max_length=500, required=False)
    category = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory = forms.CharField(widget=forms.Select(choices=()), required=False)
    source_title = forms.CharField(widget=forms.Select(choices=()), required=False)
    persistent = forms.BooleanField(required=False, initial=False)
    language = forms.CharField(label="language", max_length=500, required=False)
    user = forms.CharField(label="user", max_length=500, required=False)
    tag = forms.CharField(label="tag", max_length=500, required=False)
    date_to = forms.DateField(
        required=False, initial=datetime.now() + timedelta(days=1)
    )
    date_from = forms.DateField(
        required=False, initial=datetime.now() - timedelta(days=30)
    )

    def __init__(self, *args, **kwargs):
        self.args = kwargs.pop("args", ())
        super().__init__(*args, **kwargs)
        self.fields["date_to"].initial = datetime.now() + timedelta(days=1)
        self.fields["date_from"].initial = datetime.now() - timedelta(days=30)

    def get_filtered_objects(self):
        source_parameter_map = self.get_source_filter_args(False)
        entry_parameter_map = self.get_entry_filter_args(False)

        print("Entry parameter map: {}".format(str(entry_parameter_map)))

        self.entries = []
        self.entries = LinkDataModel.objects.filter(**entry_parameter_map)

        return self.entries

    def create(self):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form

        self.get_sources()

        categories = self.get_filtered_objects_values("category")
        subcategories = self.get_filtered_objects_values("subcategory")
        title = self.get_filtered_objects_values("title")

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        # default form value
        # https://stackoverflow.com/questions/604266/django-set-default-form-values
        category_init = self.get_source_init("category")
        subcategory_init = self.get_source_init("subcategory")
        title_init = self.get_source_init("title")

        init = {}
        init["language"] = ""
        init["persistent"] = False
        init["user"] = ""
        init["tag"] = ""
        if len(self.args) != 0:
            init["language"] = self.args.get("language")
            if "persistent" in self.cleaned_data:
                init["persistent"] = True
            init["user"] = self.args.get("user")
            init["tag"] = self.args.get("tag")

        self.fields["category"].widget = forms.Select(choices=categories, attrs=attr)
        self.fields["category"].initial = category_init
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )
        self.fields["subcategory"].initial = subcategory_init
        self.fields["source_title"].widget = forms.Select(choices=title, attrs=attr)
        self.fields["source_title"].initial = title_init
        self.fields["persistent"].initial = init["persistent"]
        self.fields["language"].initial = init["language"]
        self.fields["user"].initial = init["user"]
        self.fields["tag"].initial = init["tag"]
        self.fields["date_to"].initial = datetime.now() + timedelta(days=1)
        self.fields["date_from"].initial = datetime.now() - timedelta(days=30)

        # self.fields['language'].widget.attrs.update({"style" : "display:none"})

    def get_sources(self):
        source_parameter_map = self.get_source_filter_args(False)
        self.sources = SourceDataModel.objects.filter(**source_parameter_map)

    def get_filtered_objects_values(self, field):
        values = set()
        values.add("Any")

        if len(self.sources) > 0:
            for val in self.sources.values(field):
                if str(val).strip() != "":
                    values.add(val[field])

        dict_values = self.to_dict(values)

        return dict_values

    def get_source_init(self, column):
        filters = self.get_source_filter_args(False)
        if column in filters:
            return filters[column]
        else:
            return ""

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
            if item.strip() != "":
                if item == "Any":
                    result.append(("", item))
                else:
                    result.append((item, item))
        return result

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

    def get_entry_filter_args(self, pure_data=True):
        parameter_map = {}

        persistent = self.args.get("persistent")
        if persistent:
            persistent = True

        search = self.args.get("search")
        language = self.args.get("language")
        user = self.args.get("user")

        tag = self.args.get("tag")

        category = self.args.get("category")
        subcategory = self.args.get("subcategory")
        source_title = self.args.get("source_title")

        if pure_data:
            data = self.cleaned_data
            if "persistent" in data and not data["persistent"]:
                del data["persistent"]
            return data
        else:
            tag_key, tag = self.get_tag_search()

            if self.cleaned_data["date_from"] and self.cleaned_data["date_to"]:
                parameter_map["date_published__range"] = [
                    self.cleaned_data["date_from"],
                    self.cleaned_data["date_to"],
                ]
            if persistent:
                parameter_map["persistent"] = persistent
            if search:
                parameter_map["title__icontains"] = search
            if language:
                parameter_map["language__icontains"] = language
            if user:
                parameter_map["user"] = user
            if tag:
                parameter_map[tag_key] = tag
            if category and category != "Any":
                parameter_map["source_obj__category"] = category
            if subcategory and subcategory != "Any":
                parameter_map["source_obj__subcategory"] = subcategory
            if source_title and source_title != "Any":
                parameter_map["source_obj__title"] = source_title

        return parameter_map

    def get_tag_search(self):
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
        filters = {}
        for key in infilters:
            if (
                infilters[key] is not None
                and infilters[key] != ""
                and infilters[key] != "Any"
            ):
                filters[key] = infilters[key]

        if "cagetory" in filters and filters["category"] == "Any":
            del filters["category"]
        if "subcagetory" in filters and filters["subcategory"] == "Any":
            del filters["subcategory"]
        if "source_title" in filters and filters["source_title"] == "Any":
            del filters["source_title"]

        for filter_name in filters:
            filtervalue = filters[filter_name]
            if filtervalue and str(filtervalue).strip() == "":
                del filters[filter_name]

        filter_string = ""
        for key in filters:
            filter_string += "&{0}={1}".format(key, filters[key])

        return filter_string


class CommentEntryForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = LinkCommentDataModel
        fields = ["comment", "link", "date_published", "author"]

    def __init__(self, *args, **kwargs):
        super(CommentEntryForm, self).__init__(*args, **kwargs)
        self.fields["link"].widget.attrs["readonly"] = True
        self.fields["author"].widget.attrs["readonly"] = True

    def save_comment(self):
        link_url = self.cleaned_data["link"]

        entry = LinkDataModel.objects.get(link=link_url)

        comment = self.save(commit=False)
        comment.link_obj = entry
        comment.save()
