from datetime import datetime, timedelta, date
from django import forms
from django.db.models import Q
from django.db.models import IntegerField, Model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms.widgets import TextInput


from utils.dateutils import DateUtils

from .models import (
    BackgroundJob,
    UserTags,
    UserComments,
    UserVotes,
    UserSearchHistory,
    DomainsSuffixes,
    DomainsTlds,
    DomainsMains,
    SourceCategories,
    SourceSubCategories,
    ConfigurationEntry,
    UserConfig,
    DataExport,
    EntryRules,
    ApiKeys,
    Credentials,
    Browser,
    SearchView,
)
from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

from .configuration import Configuration
from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    DomainsController,
)


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

            self.is_mobile = ViewPage(self.request).is_mobile
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

    def to_choices(self, names):
        names = sorted(names)
        result = []

        for name in names:
            result.append([name, name])

        return result


class ConfigForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = ConfigurationEntry
        fields = [
            # important
            "instance_title",
            "instance_description",
            "instance_internet_location",
            "initialization_type",
            "admin_user",
            "logging_level",
            "view_access_type",
            "download_access_type",
            "add_access_type",
            "use_internal_scripts",
            "data_export_path",
            "data_import_path",
            "download_path",
            "auto_store_thumbnails",
            "favicon_internet_url",
            "thread_memory_threshold",
            # features
            "enable_background_jobs",
            "enable_domain_support",
            "enable_keyword_support",
            "enable_file_support",
            "enable_link_archiving",
            "enable_source_archiving",
            "keep_social_data",
            # database link contents
            "accept_domain_links",
            "accept_non_domain_links",
            "accept_ip_links",
            "accept_dead_links",
            "prefer_https_links",
            "prefer_non_www_links",
            "auto_scan_new_entries",
            "new_entries_merge_data",
            "new_entries_use_clean_data",
            "entry_update_via_internet",
            "log_remove_entries",
            "auto_create_sources",
            "default_source_state",
            # updates
            "sources_refresh_period",
            "days_to_move_to_archive",
            "days_to_remove_links",
            "days_to_remove_stale_entries",
            "days_to_check_std_entries",
            "days_to_check_stale_entries",
            "remove_entry_vote_threshold",
            "number_of_update_entries",
            # Networking
            "remote_webtools_server_location",
            "internet_status_test_url",
            # user
            "track_user_actions",
            "track_user_searches",
            "track_user_navigation",
            "max_number_of_user_search",
            "max_user_entry_visit_history",
            "vote_min",
            "vote_max",
            "number_of_comments_per_day",
            # display settings
            "time_zone",
            "display_style",
            "display_type",
            "show_icons",
            "thumbnails_as_icons",
            "small_icons",
            "entries_visit_alpha",
            "entries_dead_alpha",
            "links_per_page",
            "sources_per_page",
            "max_links_per_page",
            "max_sources_per_page",
            "max_number_of_related_links",
            # other
            "block_job_queue",
            "debug_mode",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.long_widget("instance_title")
        self.long_widget("instance_description")
        self.long_widget("instance_internet_location")
        self.long_widget("admin_user")
        self.long_widget("favicon_internet_url")
        self.long_widget("internet_status_test_url")
        self.long_widget("time_zone")
        self.long_widget("data_export_path")
        self.long_widget("data_import_path")
        self.long_widget("download_path")

    def long_widget(self, field_name):
        self.fields[field_name].widget.attrs.update(size=self.init.get_cols_size())


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
            "credentials",
            "db_user",
            "export_entries",
            "export_entries_bookmarks",
            "export_entries_permanents",
            "export_sources",
            "export_time",
            "format_json",
            "format_md",
            "format_rss",
            "format_html",
            "format_sources_opml",
            "output_zip",
            "output_sqlite",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EntryRulesForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = EntryRules
        fields = [
            "enabled",
            "rule_name",
            "trigger_rule_url",
            "trigger_text",
            "trigger_text_hits",
            "trigger_text_fields",
            "block",
            "trust",
            "auto_tag",
            "apply_age_limit",
            "browser",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["trigger_rule_url"].widget.attrs.update(
            size=self.init.get_cols_size()
        )
        self.fields["trigger_text"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["trigger_text_fields"].widget.attrs.update(
            size=self.init.get_cols_size()
        )


class SearchViewForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = SearchView
        fields = [
            "name",
            "default",
            "hover_text",
            "filter_statement",
            "icon",
            "order_by",
            "entry_limit",
            "auto_fetch",
            "date_published_day_limit",
            "date_created_day_limit",
            "user",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["hover_text"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["filter_statement"].widget.attrs.update(
            size=self.init.get_cols_size()
        )
        self.fields["icon"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["order_by"].widget.attrs.update(size=self.init.get_cols_size())


class ApiKeysForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = ApiKeys
        fields = [
            "key",
            "user",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class CredentialsForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = Credentials
        fields = [
            "name",
            "credential_type",
            "username",
            "password",
            "token",
            "secret",
            "owner",
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
    import_ids = forms.BooleanField(required=False)

    username = forms.CharField(max_length=500, required=False)
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
        self.fields["link"].widget.attrs["placeholder"] = "Input URL"
        self.fields["link"].widget.attrs["autofocus"] = True

    def get_information(self):
        return self.cleaned_data


class LinkPropertiesForm(forms.Form):
    link = forms.CharField(label="Link", max_length=500)
    browser = forms.IntegerField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["link"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["link"].widget.attrs["placeholder"] = "Input URL"
        self.fields["link"].widget.attrs["autofocus"] = True

        browsers = self.get_browser_choices()
        self.fields["browser"].widget = forms.Select(choices=browsers)

    def get_browser_choices(self):
        result = []

        result.append([Browser.AUTO, "Automatic"])

        browsers = Browser.objects.filter(enabled=True).values("id", "name")
        for browser in browsers:
            result.append([browser["id"], browser["name"]])

        return result

    def get_information(self):
        return self.cleaned_data


class AddEntryForm(forms.Form):
    link = forms.CharField(label="Link", max_length=500)
    browser = forms.IntegerField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["link"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["link"].widget.attrs["placeholder"] = "Input URL"
        self.fields["link"].widget.attrs["autofocus"] = True

        browsers = self.get_browser_choices()
        self.fields["browser"].widget = forms.Select(choices=browsers)

    def get_browser_choices(self):
        result = []
        result.append([Browser.AUTO, "Automatic"])

        browsers = Browser.objects.filter(enabled=True).values("id", "name")
        for browser in browsers:
            result.append([browser["id"], browser["name"]])

        result.append([Browser.EMPTY_FORM, "Empty form"])

        return result

    def get_information(self):
        return self.cleaned_data


class SourceInputForm(forms.Form):
    url = forms.CharField(label="Source URL", max_length=500)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.fields["url"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["url"].widget.attrs["placeholder"] = "Input URL"
        self.fields["url"].widget.attrs["autofocus"] = True

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

        self.fields["url"].widget.attrs["placeholder"] = "Input URL"


class ExportTopicForm(forms.Form):
    tag = forms.CharField(label="Tag", max_length=500)
    store_domain_info = forms.BooleanField()


class TagForm(forms.Form):
    """
    Tag links form
    """

    tag = forms.CharField(label="Tag name", max_length=500)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["tag"].widget.attrs["autofocus"] = True


class InitSearchForm(forms.Form):
    """
    Omni search form
    """

    search = forms.CharField(label="", max_length=500, required=False)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)

        scope = kwargs.pop("scope", "")
        auto_fetch = kwargs.pop("auto_fetch", "")

        super().__init__(*args, **kwargs)

        self.fields["search"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["search"].widget.attrs["autofocus"] = True
        self.fields["search"].help_text = scope


class OmniSearchForm(forms.Form):
    """
    Omni search form
    """

    search = forms.CharField(
        label="Search",
        max_length=500,
        required=False,
        widget=TextInput(
            attrs={
                "placeholder": "Type to search...",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        self.search_history = self.init.pop_data(args, kwargs, "user_choices")

        super().__init__(*args, **kwargs)

        self.fields["search"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["search"].widget.attrs["autofocus"] = True


class OmniSearchWithArchiveForm(OmniSearchForm):
    """
    Omni search with archive links form
    """

    archive = forms.BooleanField(label="Search archive", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class EntryForm(forms.ModelForm):
    """
    Used to edit entry
    """

    class Meta:
        model = LinkDataController
        fields = [
            "link",
            "title",
            "description",
            "date_published",
            "source_url",
            "permanent",
            "language",
            "user",
            "author",
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
        self.fields["source_url"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["thumbnail"].widget.attrs.update(size=self.init.get_cols_size())

        self.fields["link"].required = True
        self.fields["source_url"].required = False
        self.fields["language"].required = False
        self.fields["description"].required = False
        self.fields["title"].required = False
        self.fields["author"].required = False
        self.fields["album"].required = False
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
            "source_url",
            "language",
            "user",
            "author",
            "album",
            "age",
            "thumbnail",
        ]
        widgets = {
            #    'date_published': forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class SourceForm(forms.ModelForm):
    """
    Used to edit sources
    """

    class Meta:
        model = SourceDataController
        fields = [
            "url",
            "enabled",
            "title",
            "source_type",
            "category_name",
            "subcategory_name",
            "language",
            "age",
            "export_to_cms",
            "fetch_period",
            "remove_after_days",
            "auto_tag",
            "entries_alpha",
            "entries_backgroundcolor",
            "favicon",
            "auto_update_favicon",
            "credentials",
            "proxy_location",
        ]
        widgets = {}

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        self.fields["url"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["favicon"].widget.attrs.update(size=self.init.get_cols_size())

        self.fields["entries_backgroundcolor"].widget = forms.TextInput(attrs={"type" : "color", "value" : ""})

        names = SourceControllerBuilder.get_plugin_names()
        # self.fields["source_type"].widget = forms.Select(choices=self.to_choices(names))

    def to_choices(self, names):
        names = sorted(names)
        result = []

        for name in names:
            result.append([name, name])

        return result


class TagEditForm(forms.Form):
    tags = forms.CharField(
        label="Edit",
        widget=forms.TextInput(
            attrs={"placeholder": "Enter tags, separated by commas", "id": "id_tag"}
        ),
        max_length=255,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)

        super().__init__(*args, **kwargs)
        self.fields["tags"].widget.attrs["autofocus"] = True
        self.fields["tags"].widget.attrs.update(size=self.init.get_cols_size())


class TagRenameForm(forms.Form):
    """
    Category choice form
    """

    current_tag = forms.CharField(label="Current tag", max_length=100)
    new_tag = forms.CharField(label="New tag", max_length=100)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["new_tag"].widget.attrs["autofocus"] = True


class BackgroundJobForm(forms.Form):
    job = forms.CharField(
        widget=forms.Select(choices=BackgroundJob.JOB_CHOICES), required=True
    )
    subject = forms.CharField(label="subject", required=False)
    args = forms.CharField(label="args", required=False)
    task = forms.CharField(label="task", required=False)


class DomainEditForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = DomainsController
        fields = [
            "domain",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
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
    category_name = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory_name = forms.CharField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)

        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        categories = self.get_categories()
        subcategories = self.get_subcategories()

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        self.fields["category_name"].widget = forms.Select(
            choices=categories, attrs=attr
        )
        self.fields["subcategory_name"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )
        self.fields["search"].widget.attrs["placeholder"] = "Search..."
        self.fields["search"].widget.attrs["autofocus"] = True
        self.fields["search"].widget.attrs.update(size=self.init.get_cols_size())

    def get_categories(self):
        result = []
        result.append(["", ""])

        for category in SourceCategories.objects.all():
            result.append([category.name, category.name])

        return result

    def get_subcategories(self):
        result = []
        result.append(["", ""])

        for subcategory in SourceSubCategories.objects.all():
            result.append([subcategory.name, subcategory.name])

        return result


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
        super().__init__(*args, **kwargs)

        config = Configuration.get_object().config_entry

        self.fields["vote"].validators = [
            MaxValueValidator(config.vote_max),
            MinValueValidator(config.vote_min),
        ]
        self.fields["vote"].widget.attrs["autofocus"] = True


class BrowserEditForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = Browser
        fields = [
            "enabled",
            "name",
            "priority",
            "crawler",
            "settings",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["crawler"].widget.attrs["readonly"] = True

        self.fields["settings"].widget = forms.Textarea(attrs={"rows": 10, "cols": 20})
