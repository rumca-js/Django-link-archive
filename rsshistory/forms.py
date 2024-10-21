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
    Browser,
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

            self.is_mobile = ViewPage(self.request).is_mobile()
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
            "instance_title",
            "instance_description",
            "instance_internet_location",
            "admin_user",
            "access_type",
            "download_access_type",
            "add_access_type",
            "logging_level",
            "background_tasks",
            "user_internal_scripts",
            "data_export_path",
            "data_import_path",
            "download_path",
            "auto_store_thumbnails",
            "favicon_internet_location",
            # features
            "enable_domain_support",
            "enable_keyword_support",
            "enable_file_support",
            "link_save",
            "source_save",
            # database link contents
            "accept_dead",
            "accept_ip_addresses",
            "accept_domains",
            "accept_not_domain_entries",
            "keep_domains",
            "keep_permanent_items",
            "auto_scan_entries",
            "new_entries_merge_data",
            "new_entries_use_clean_data",
            "auto_create_sources",
            "new_source_enabled_state",
            "prefer_https",
            "prefer_non_www_sites",
            "block_keywords",
            # updates
            "sources_refresh_period",
            "days_to_move_to_archive",
            "days_to_remove_links",
            "days_to_remove_stale_entries",
            "days_to_check_std_entries",
            "days_to_check_stale_entries",
            "number_of_update_entries",
            # Networking
            "ssl_verification",
            "user_agent",
            "user_headers",
            "internet_test_page",
            "respect_robots_txt",
            # user
            "track_user_actions",
            "track_user_searches",
            "track_user_navigation",
            "max_number_of_searches",
            "vote_min",
            "vote_max",
            "number_of_comments_per_day",
            # display settings
            "time_zone",
            "whats_new_days",
            "entries_order_by",
            "display_style",
            "display_type",
            "show_icons",
            "thumbnails_as_icons",
            "small_icons",
            "links_per_page",
            "sources_per_page",
            "max_links_per_page",
            "max_sources_per_page",
            "max_number_of_related_links",
            # other
            "debug_mode",
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
            "rule_url",
            "block",
            "auto_tag",
            "requires_headless",
            "requires_full_browser",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


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
        self.fields["link"].widget.attrs["placeholder"] = "Input URL"
        self.fields["link"].widget.attrs["autofocus"] = True

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
        super().__init__(*args, **kwargs)

        attr = {"onchange": "this.form.submit()"}
        self.fields["search"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["search"].widget.attrs["autofocus"] = True


# TODO support for datalist in form....

#from django.utils.safestring import mark_safe
#import json
#import html
#
#
#class DatalistTextInput(TextInput):
#    def __init__(self, attrs=None):
#        super().__init__(attrs)
#        if "list" not in self.attrs or "datalist" not in self.attrs:
#            raise ValueError(
#                'DatalistTextInput widget is missing required attrs "list" or "datalist"'
#            )
#        self.datalist_name = self.attrs["list"]
#
#        text = self.attrs.pop("datalist")
#        self.datalist = text
#
#    def render(self, **kwargs):
#        datalist = self.datalist
#
#        print("render kwargs:{}".format(kwargs))
#
#        # DEBUG( self, kwargs)
#        original_part = super().render(**kwargs)
#
#        opts = " ".join([f"<option>{x}</option>" for x in datalist])
#
#        part2 = f'<datalist id="{self.datalist_name}">{opts}</datalist>'
#
#        return original_part + part2


class OmniSearchForm(forms.Form):
    """
    Omni search form
    """

    search = forms.CharField(
        label="Search",
        max_length=500,
        required=False,
        widget=TextInput(
            attrs={"list": "", "datalist": [], "placeholder": "Type to search..."}
        ),
    )

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        full_search_history = self.init.pop_data(args, kwargs, "user_choices")

        search_history = []
        if full_search_history:
            for search in full_search_history:
                search_history.append(search.search_query)

        super().__init__(*args, **kwargs)

        attr = {"onchange": "this.form.submit()"}

        self.fields["search"].widget = TextInput(
            attrs={
                "list": "foolist",
                "datalist": search_history,
                "placeholder": "Type to search...",
            }
        )
        self.fields["search"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["search"].widget.attrs["autofocus"] = True

        if self.init.is_mobile:
            # TODO setting size does not work
            # self.fields["search_history"].widget.attrs.update(size="10")
            # self.fields["search_history"].widget.attrs.update(width="100%")
            # self.fields["search_history"].widget.attrs.update(width="10px")
            pass


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
        self.fields["source_url"].widget.attrs.update(size=self.init.get_cols_size())
        self.fields["thumbnail"].widget.attrs.update(size=self.init.get_cols_size())

        self.fields["link"].required = True
        self.fields["source_url"].required = False
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
            "source_url",
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
    Used to edit sources
    """

    class Meta:
        model = SourceDataController
        fields = [
            "url",
            "enabled",
            "title",
            "source_type",
            "auto_tag",
            "category_name",
            "subcategory_name",
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


class TagEditForm(forms.Form):
    tags = forms.CharField(
        label='Edit',
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter tags, separated by commas',
            'id': 'id_tag'
        }),
        max_length=255,
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["link"].widget.attrs.update(size=self.init.get_cols_size())


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

    def create(self):
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
            "mode",
            "crawler",
            "settings",
        ]

    def __init__(self, *args, **kwargs):
        self.init = UserRequest(args, kwargs)
        super().__init__(*args, **kwargs)
        self.fields["crawler"].widget.attrs["readonly"] = True

        self.fields["settings"].widget = forms.Textarea(
            attrs={"rows": 10, "cols": 20}
        )
