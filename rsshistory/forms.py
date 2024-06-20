from datetime import datetime, timedelta, date
from django import forms
from django.db.models import Q
from django.db.models import IntegerField, Model
from django.core.validators import MaxValueValidator, MinValueValidator


from .models import (
    BackgroundJob,
    UserTags,
    LinkCommentDataModel,
    UserVotes,
    UserSearchHistory,
)
from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder
from .models import DomainsSuffixes
from .models import DomainsTlds
from .models import DomainsMains
from .models import SourceCategories
from .models import SourceSubCategories
from .models import ConfigurationEntry, UserConfig, DataExport, EntryRule

from .configuration import Configuration
from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    DomainsController,
)
from .dateutils import DateUtils


# https://docs.djangoproject.com/en/4.1/ref/forms/widgets/


def my_date_to():
    return DateUtils.get_days_range()[1]


def my_date_from():
    return DateUtils.get_days_range()[0]


class UserRequest(object):
    def __init__(self, args, kwargs):
        self.pop_headers(args, kwargs)

    def pop_headers(self, args, kwargs):
        self.request = None
        self.is_mobile = False

        self.request = self.pop_data(args, kwargs, "request")
        if self.request:
            from .views import ViewPage

            self.is_mobile = ViewPage.is_mobile(self.request)
            self.user = self.request.user

    def pop_data(self, args, kwargs, data):
        if data in kwargs:
            return kwargs.pop(data)

    def get_cols_size(self):
        if self.is_mobile:
            return "30"
        else:
            return "100"

    def get_long_input_size(self):
        if self.is_mobile:
            return "30"
        else:
            return "100"

    def get_submit_attrs(self):
        attr = {"onchange": "this.form.submit()"}


class ConfigForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = ConfigurationEntry
        fields = [
            # important
            "background_task",
            "ssl_verification",
            "access_type",
            "admin_user",
            "data_export_path",
            "data_import_path",
            #
            "enable_domain_support",
            "enable_keyword_support",
            "enable_file_support",
            "accept_dead",
            "accept_ip_addresses",
            "accept_domains",
            "accept_not_domain_entries",
            "auto_scan_entries",
            "new_entries_merge_data",
            "new_entries_use_clean_data",
            "auto_create_sources",
            "new_source_enabled_state",
            # updates
            "sources_refresh_period",
            "days_to_move_to_archive",
            "days_to_remove_links",
            "days_to_remove_stale_entries",
            "days_to_check_std_entries",
            "days_to_check_stale_entries",
            "number_of_update_entries",
            "block_keywords",
            # optional
            "prefer_https",
            "link_save",
            "source_save",
            # user
            "track_user_actions",
            "track_user_searches",
            "track_user_navigation",
            "vote_min",
            "vote_max",
            # display settings
            "whats_new_days",
            "time_zone",
            "entries_order_by",
            "number_of_comments_per_day",
            "display_style",
            "display_type",
            "show_icons",
            "thumbnails_as_icons",
            "small_icons",
            "links_per_page",
            "sources_per_page",
            "max_links_per_page",
            "max_sources_per_page",
            # Advanced
            "user_agent",
            "user_headers",
            "internet_test_page",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.fields["user_agent"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["block_keywords"].widget.attrs.update(
            size=self.init.get_cols_size()
        )

        if self.init.is_mobile:
            self.fields["user_headers"].widget = forms.Textarea(
                attrs={"rows": 10, "cols": 20}
            )
        else:
            self.fields["user_headers"].widget = forms.Textarea(
                attrs={"rows": 20, "cols": 75}
            )


class DataExportForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = DataExport
        fields = [
            "enabled",
            "export_type",
            "export_data",
            "local_path",
            "remote_path",
            "user",
            "password",
            "db_user",
            "export_entries",
            "export_entries_bookmarks",
            "export_entries_permanents",
            "export_sources",
            "export_time",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EntryRuleForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = EntryRule
        fields = [
            "enabled",
            "rule_name",
            "rule_url",
            "block",
            "auto_tag",
            "requires_selenium",
            "requires_selenium_full",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserConfigForm(forms.ModelForm):
    """
    Category choice form
    """

    # BIRTH_YEAR_CHOICES = ["1970", "]

    class Meta:
        model = UserConfig
        fields = [
            "show_icons",
            "thumbnails_as_icons",
            "small_icons",
            "display_type",
            "display_style",
            "links_per_page",
            "sources_per_page",
            "birth_date",
        ]
        # fields = ['show_icons', 'thumbnails_as_icons', 'small_icons', 'display_type', 'theme', 'links_per_page']
        # widgets = {
        # }
        # widgets = {
        #    # DateTimeInput widget does not work my my Android phone
        #        'birth_date': forms.SelectDateWidget(years=BIRTH_YEAR_CHOICES)
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ImportSourceRangeFromInternetArchiveForm(forms.Form):
    source_url = forms.CharField(max_length=500)
    archive_start = forms.DateField(label="Start time")
    archive_stop = forms.DateField(label="Stop time")


class ImportFromFilesForm(forms.Form):
    path = forms.CharField(max_length=500)

    import_entries = forms.BooleanField(required=False)
    import_sources = forms.BooleanField(required=False)
    import_title = forms.BooleanField(required=False)
    import_description = forms.BooleanField(required=False)
    import_tags = forms.BooleanField(required=False)
    import_comments = forms.BooleanField(required=False)
    import_votes = forms.BooleanField(required=False)
    import_bookmarks = forms.BooleanField(required=False)

    user = forms.CharField(max_length=500, required=False)
    tag = forms.CharField(max_length=500, required=False)


class ExportDailyDataForm(forms.Form):
    time_start = forms.DateField(label="Start time")
    time_stop = forms.DateField(label="Stop time")


class KeywordInputForm(forms.Form):
    keyword = forms.DateField(label="Keyword")


class PushDailyDataForm(forms.Form):
    input_date = forms.DateField(label="Input date", initial=my_date_from)


class LinkInputForm(forms.Form):
    link = forms.CharField(label="Link", max_length=500)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["link"].widget.attrs.update(size=self.init.get_cols_size())

    def get_information(self):
        return self.cleaned_data


class SourceInputForm(forms.Form):
    url = forms.CharField(label="Source URL", max_length=500)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.fields["url"].widget.attrs.update(size=self.init.get_cols_size())

    def get_information(self):
        return self.cleaned_data


class ScannerForm(forms.Form):
    # fmt: off
    body = forms.CharField(widget=forms.Textarea(attrs={'rows':30, 'cols':75}))
    tag = forms.CharField(label="tag", max_length=500, help_text="Tag is set for each added entry. Tag can be empty", required=False)
    # fmt: on

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)


class ContentsForm(forms.Form):
    # fmt: off
    body = forms.CharField(widget=forms.Textarea(attrs={'rows':30, 'cols':75}))
    # fmt: on

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)


class UrlContentsForm(forms.Form):
    # fmt: off
    url = forms.CharField(label="Source URL", max_length=500)
    body = forms.CharField(widget=forms.Textarea(attrs={'rows':30, 'cols':75}))
    # fmt: on

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)


class ExportTopicForm(forms.Form):
    tag = forms.CharField(label="Tag", max_length=500)
    store_domain_info = forms.BooleanField()


class TagForm(forms.Form):
    """
    Tag links form
    """

    tag = forms.CharField(label="Tag name", max_length=500)


class YouTubeLinkSimpleForm(forms.Form):
    """
    links form
    """

    youtube_link = forms.CharField(label="YouTube Link URL", max_length=500)


class OmniSearchForm(forms.Form):
    """
    Omni search form
    """

    search = forms.CharField(label="Search for", max_length=500, required=False)
    search_history = forms.CharField(widget=forms.Select(choices=[]), required=False)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        user_choices = self.init.pop_data(args, kwargs, "user_choices")
        if not user_choices:
            user_choices = []
        user_choices = OmniSearchForm.get_user_choices(user_choices)

        super().__init__(*args, **kwargs)

        attr = {"onchange": "this.form.submit()"}
        self.fields["search_history"].widget = forms.Select(
            choices=user_choices, attrs=attr
        )

        self.fields["search"].widget.attrs.update(size=self.init.get_cols_size())

        if self.init.user:
            if not self.init.user.is_authenticated:
                self.fields["search_history"].widget = forms.HiddenInput()

        if self.init.is_mobile:
            # TODO setting size does not work
            # self.fields["search_history"].widget.attrs.update(size="10")
            # self.fields["search_history"].widget.attrs.update(width="100%")
            # self.fields["search_history"].widget.attrs.update(width="10px")
            pass

    def set_choices(self, choices):
        self.fields["search_history"].widget = forms.Select(choices=choices)

    def get_user_choices(choices):
        result = []
        result.append([None, None])

        for row, choice in enumerate(choices):
            limit = OmniSearchForm.get_search_history_length()
            if len(choice) > limit:
                new_choice = choice[:limit] + "(...)"
            else:
                new_choice = choice
            # result.append([choice, new_choice])
            result.append([choice, choice])

        return result

    def get_search_history_length():
        return 30


class OmniSearchWithArchiveForm(OmniSearchForm):
    """
    Omni search with archive links form
    """

    archive = forms.BooleanField(label="Search archive", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.init.user:
            if not self.init.user.is_authenticated:
                self.fields["search_history"].widget = forms.HiddenInput()


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
            "bookmarked",
            "permanent",
            "language",
            "user",
            "artist",
            "album",
            "age",
            "thumbnail",
            "manual_status_code",
            # automatic data. readonly
            "status_code",
            "page_rating",
            "page_rating_contents",
            "page_rating_votes",
        ]
        widgets = {
            # DateTimeInput widget does not work my my Android phone
            #    'date_published': forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'})
        }

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.fields["link"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["title"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["source"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["thumbnail"].widget.attrs.update(size=self.init.get_cols_size())

        self.fields["link"].required = True
        self.fields["source"].required = False
        self.fields["language"].required = False
        self.fields["description"].required = False
        self.fields["title"].required = False
        self.fields["artist"].required = False
        self.fields["album"].required = False
        self.fields["bookmarked"].initial = True
        self.fields["user"].widget.attrs["readonly"] = True
        self.fields["age"].required = False
        self.fields["thumbnail"].required = False
        self.fields["manual_status_code"].required = False

        self.fields["status_code"].widget.attrs["readonly"] = True
        self.fields["page_rating"].widget.attrs["readonly"] = True
        self.fields["page_rating_votes"].widget.attrs["readonly"] = True
        self.fields["page_rating_contents"].widget.attrs["readonly"] = True

    def get_information(self):
        return self.cleaned_data


class EntryArchiveForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = ArchiveLinkDataController
        fields = [
            "link",
            "title",
            "description",
            "date_published",
            "source",
            "bookmarked",
            "language",
            "user",
            "artist",
            "album",
            "age",
            "thumbnail",
        ]
        widgets = {
            #    'date_published': forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class SourceForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = SourceDataController
        fields = [
            "url",
            "enabled",
            "title",
            "source_type",
            "auto_tag",
            "category",
            "subcategory",
            "language",
            "age",
            "fetch_period",
            "export_to_cms",
            "remove_after_days",
            "favicon",
            "proxy_location",
        ]
        widgets = {}

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.fields["url"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["favicon"].widget.attrs.update(size=self.init.get_cols_size())

        # TODO thing below should be handled by model properties
        self.fields["favicon"].required = False
        self.fields["proxy_location"].required = False

        names = SourceControllerBuilder.get_plugin_names()
        self.fields["source_type"].widget = forms.Select(choices=self.to_choices(names))

    def to_choices(self, names):
        names = sorted(names)
        result = []

        for name in names:
            result.append([name, name])

        return result


class TagEntryForm(forms.Form):
    """
    Category choice form
    TODO remake to standard form?
    """

    entry_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    tag = forms.CharField(max_length=1000)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.fields["tag"].widget.attrs.update(size=self.init.get_cols_size())


class TagRenameForm(forms.Form):
    """
    Category choice form
    """

    current_tag = forms.CharField(label="Current tag", max_length=100)
    new_tag = forms.CharField(label="New tag", max_length=100)


class BackgroundJobForm(forms.Form):
    job = forms.CharField(
        widget=forms.Select(choices=BackgroundJob.JOB_CHOICES), required=True
    )
    task = forms.CharField(label="task", required=False)
    subject = forms.CharField(label="subject", required=False)
    args = forms.CharField(label="args", required=False)


class DomainEditForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = DomainsController
        fields = [
            "domain",
            "dead",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super(DomainEditForm, self).__init__(*args, **kwargs)
        self.fields["domain"].widget.attrs["readonly"] = True


class DomainsChoiceForm(forms.Form):
    """
    Category choice form
    """

    search = forms.CharField(label="Search", max_length=500, required=False)
    suffix = forms.CharField(widget=forms.Select(choices=()), required=False)
    tld = forms.CharField(widget=forms.Select(choices=()), required=False)
    sort = forms.CharField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        self.fields["suffix"].widget = forms.Select(
            choices=self.get_suffix_choices(), attrs=attr
        )
        self.fields["tld"].widget = forms.Select(
            choices=self.get_tld_choices(), attrs=attr
        )
        self.fields["sort"].widget = forms.Select(
            choices=self.get_sort_choices(), attrs=attr
        )

    def to_choices(self, names):
        names = sorted(names)
        result = []

        for name in names:
            result.append([name, name])

        return result

    def get_suffix_choices(self):
        result = []
        result.append("")

        suffs = DomainsSuffixes.objects.all()
        for suff in suffs:
            if suff and suff != "":
                result.append(suff.suffix)

        return self.to_choices(result)

    def get_tld_choices(self):
        result = []
        result.append("")

        tlds = DomainsTlds.objects.all()
        for tld in tlds:
            if tld and tld != "":
                result.append(tld.tld)

        return self.to_choices(result)

    def get_main_choices(self):
        result = []
        result.append("")

        mains = DomainsMains.objects.all()
        for main in mains and main != "":
            result.append(main.main)

        return self.to_choices(result)

    def get_sort_choices(self):
        names = DomainsController.get_query_names()
        names.append("")
        return self.to_choices(names)


class SourcesChoiceForm(forms.Form):
    """
    Category choice form
    """

    search = forms.CharField(label="Search", max_length=500, required=False)
    category = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory = forms.CharField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

    def create(self):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        categories = self.get_categories()
        subcategories = self.get_subcategories()

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        self.fields["category"].widget = forms.Select(choices=categories, attrs=attr)
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )

    def get_categories(self):
        result = []
        result.append(["", ""])

        for category in SourceCategories.objects.all():
            result.append([category.category, category.category])

        return result

    def get_subcategories(self):
        result = []
        result.append(["", ""])

        for subcategory in SourceSubCategories.objects.all():
            result.append([subcategory.subcategory, subcategory.subcategory])

        return result


class BasicEntryChoiceForm(forms.Form):
    search = forms.CharField(label="Search", max_length=1000, required=False)
    category = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory = forms.CharField(widget=forms.Select(choices=()), required=False)
    # fmt: off
    source_id = forms.CharField(label="Source", widget=forms.Select(choices=()), required=False)
    # fmt: on

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

    def create(self, sources):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        condition1 = Q(enabled=True)  # & Q(proxy_location = "")
        self.sources = SourceDataController.objects.filter(condition1)

        category_choices = self.get_sources_values("category")
        subcategory_choices = self.get_sources_values("subcategory")
        title_choices = self.get_sources_ids_values("title")

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        self.fields["category"].widget = forms.Select(
            choices=category_choices, attrs=attr
        )
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategory_choices, attrs=attr
        )
        self.fields["source_id"].widget = forms.Select(
            choices=title_choices, attrs=attr
        )

        self.fields["search"].widget.attrs.update(size=self.init.get_cols_size())

    def get_categories(self):
        result = []
        result.append(["", ""])

        for category in SourceCategories.objects.filter(enabled=True):
            if category and category != "":
                result.append([category.category, category.category])

        return result

    def get_subcategories(self):
        result = []
        result.append(["", ""])

        for subcategory in SourceSubCategories.objects.filter(enabled=True):
            if subcategory and subcategory != "":
                result.append([subcategory.subcategory, subcategory.subcategory])

        return result

    def get_sources_values(self, field):
        values = set()
        values.add("")

        if self.sources.count() > 0:
            for val in self.sources.values(field):
                values.add(val[field])

        dict_values = self.to_dict(values)

        return dict_values

    def get_sources_ids_values(self, field):
        values = []
        values.append(("", ""))

        if self.sources.count() > 0:
            for atuple in self.sources.values_list("id", field):
                new_val = atuple[1]

                if self.init.is_mobile:
                    if len(new_val) > 25:
                        new_val = new_val[:25] + "(...)"

                values.append([atuple[0], new_val])

        return values

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
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


class EntryRecentChoiceForm(BasicEntryChoiceForm):
    pass


class EntryChoiceForm(BasicEntryChoiceForm):
    """
    Category choice form
    """

    # do not think too much about these settings, these will be overriden by 'create' method
    title = forms.CharField(label="title", max_length=1000, required=False)
    bookmarked = forms.BooleanField(required=False, initial=False)
    language = forms.CharField(label="language", max_length=10, required=False)
    user = forms.CharField(label="user", max_length=500, required=False)
    tag = forms.CharField(label="tag", max_length=500, required=False)
    vote = forms.IntegerField(label="vote", required=False)
    artist = forms.CharField(label="artist", max_length=1000, required=False)
    album = forms.CharField(label="album", max_length=1000, required=False)
    date_to = forms.DateField(required=False, initial=my_date_to)
    date_from = forms.DateField(required=False, initial=my_date_from)
    archive = forms.BooleanField(required=False, initial=False)


class CommentEntryForm(forms.Form):
    """
    Category choice form
    Using forms not model forms, because we would have to passe link somehow
    """

    entry_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    user_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    user = forms.CharField(max_length=1000)

    comment = forms.CharField(widget=forms.Textarea)
    date_published = forms.DateTimeField(
        initial=datetime.now,
        widget=forms.widgets.DateTimeInput(
            attrs={"type": "datetime-local", "readonly": "readonly"}
        ),
    )


class LinkVoteForm(forms.Form):
    """
    Category choice form
    """

    entry_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    vote = forms.IntegerField(initial=0)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super(LinkVoteForm, self).__init__(*args, **kwargs)

        config = Configuration.get_object().config_entry

        self.fields["vote"].validators = [
            MaxValueValidator(config.vote_max),
            MinValueValidator(config.vote_min),
        ]
