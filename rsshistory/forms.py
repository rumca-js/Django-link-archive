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
from .models import ConfigurationEntry, UserConfig, DataExport
from .configuration import Configuration
from .controllers import (
    SourceDataController,
    LinkDataController,
    ArchiveLinkDataController,
    DomainsController,
)


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
            # important
            "background_task",
            "ssl_verification",
            "sources_refresh_period",
            "access_type",
            "admin_user",
            # optional
            "link_save",
            "source_save",
            "auto_scan_new_entries",
            "auto_store_entries",
            "auto_store_entries_use_all_data",
            "auto_store_entries_use_clean_page_info",
            "auto_store_sources",
            "auto_store_sources_enabled",
            "auto_store_domain_info",
            "auto_store_keyword_info",
            "track_user_actions",
            "track_user_searches",
            "track_user_navigation",
            "data_export_path",
            "data_import_path",
            "days_to_move_to_archive",
            "days_to_remove_links",
            "whats_new_days",
            "vote_min",
            "vote_max",
            # display settings
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
            #Advanced
            "user_agent",
            "user_headers",
        ]

    def __init__(self, *args, **kwargs):
        self.pop_headers(args, kwargs)

        super(ConfigForm, self).__init__(*args, **kwargs)

        # fmt: off
        self.fields["background_task"].help_text = "Informs system that background task, like celery is operational."
        self.fields["link_save"].help_text = "Links are saved using archive.org."
        self.fields["source_save"].help_text = "Links are saved using archive.org."
        self.fields["user_agent"].help_text = "You can check your user agent in <a href=\"https://www.supermonitoring.com/blog/check-browser-http-headers/\">https://www.supermonitoring.com/blog/check-browser-http-headers/</a>."
        self.fields["user_headers"].help_text = "Provide JSON configuration of headers. You can check your user agent in <a href=\"https://www.supermonitoring.com/blog/check-browser-http-headers/\">https://www.supermonitoring.com/blog/check-browser-http-headers/</a>."
        self.fields["access_type"].help_text = "There are three access types available. \"All\" allows anybody view contents. \"Logged\" allows only logged users to view contents. \"Owner\" means application is private, and only owner can view it's contents."
        self.fields["days_to_move_to_archive"].help_text = "Changing number of days after which links are moved to archive may lead to an issue. If the new number of days is smaller, links are not moved from archive back to the link table at hand."
        self.fields["auto_store_sources"].help_text = "Sources can be automatically added, if a new 'domain' information is captured. The state of such state is determined by 'Auto sources enabled' property."
        self.fields["number_of_comments_per_day"].help_text = "The limit is for each user."
        self.fields["track_user_actions"].help_text = "Among tracked elements: what is searched."
        self.fields["entries_order_by"].help_text = "For Google-like experience set -page_rating. By default it is set to order of publication, -date_published."
        self.fields["links_per_page"].label = "Number of links per page"
        self.fields["sources_per_page"].label = "Number of sources per page"
        # fmt: on

        if self.is_mobile:
            self.fields["user_agent"].widget.attrs.update(size="20")
            self.fields["user_headers"].widget=forms.Textarea(attrs={'rows':10, 'cols':20})
        else:
            self.fields["user_agent"].widget.attrs.update(size="100")
            self.fields["user_headers"].widget=forms.Textarea(attrs={'rows':20, 'cols':75})

    def pop_headers(self, args, kwargs):
        self.request = None
        self.is_mobile = False

        if "request" in kwargs:
            from .views import ViewPage

            self.request = kwargs.pop("request")
            self.is_mobile = ViewPage.is_mobile(self.request)


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
            "export_entries",
            "export_entries_bookmarks",
            "export_entries_permanents",
            "export_sources",
        ]

    def __init__(self, *args, **kwargs):
        super(DataExportForm, self).__init__(*args, **kwargs)

        # fmt: off
        self.fields["remote_path"].help_text = "Can be empty"
        self.fields["user"].help_text = "Can be empty"
        self.fields["password"].help_text = "Can be empty"
        self.fields["local_path"].help_text = "Local path is relative to main configuration export path"
        self.fields["export_entries_bookmarks"].help_text = "Export entries has to be checked for this to work"
        self.fields["export_entries_permanents"].help_text = "Export entries has to be checked for this to work"


class UserConfigForm(forms.ModelForm):
    """
    Category choice form
    """
    #BIRTH_YEAR_CHOICES = ["1970", "]

    def __init__(self, *args, **kwargs):
        super(UserConfigForm, self).__init__(*args, **kwargs)

        # TODO this does not seem to work
        self.fields["birth_date"].initial = my_date_to

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
        #widgets = {
        #    # DateTimeInput widget does not work my my Android phone
        #        'birth_date': forms.SelectDateWidget(years=BIRTH_YEAR_CHOICES)
        #}


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

    def get_information(self):
        return self.cleaned_data


class SourceInputForm(forms.Form):
    url = forms.CharField(label="Source URL", max_length=500)

    def get_information(self):
        return self.cleaned_data


class ScannerForm(forms.Form):
    # fmt: off
    body = forms.CharField(widget=forms.Textarea(attrs={'rows':30, 'cols':75}))
    tag = forms.CharField(label="tag", max_length=500, help_text="Tag is set for each added entry. Tag can be empty", required=False)
    # fmt: on


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
        self.pop_headers(args, kwargs)

        user_choices = [[None, None]]

        if "user_choices" in kwargs:
            user_choices = kwargs.pop("user_choices")
            user_choices = OmniSearchForm.get_user_choices(user_choices)

        super().__init__(*args, **kwargs)

        if not self.is_mobile:
            self.fields["search"].widget.attrs.update(size="100")
        else:
            # mobile
            self.fields["search_history"].widget.attrs.update(size="30")

        attr = {"onchange": "this.form.submit()"}
        self.fields["search_history"].widget = forms.Select(
            choices=user_choices, attrs=attr
        )

    def pop_headers(self, args, kwargs):
        self.request = None
        self.is_mobile = False

        if "request" in kwargs:
            from .views import ViewPage

            self.request = kwargs.pop("request")
            self.is_mobile = ViewPage.is_mobile(self.request)

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
            "dead",
            "language",
            "user",
            "artist",
            "album",
            "age",
            "thumbnail",
            "page_rating_contents",
        ]
        widgets = {
            # DateTimeInput widget does not work my my Android phone
            #    'date_published': forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'})
        }

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
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
            "on_hold",
            "title",
            "source_type",
            "category",
            "subcategory",
            "language",
            "fetch_period",
            "export_to_cms",
            "remove_after_days",
            "favicon",
            "proxy_location",
        ]
        widgets = {}

    def __init__(self, *args, **kwargs):
        from .pluginsources.sourcecontrollerbuilder import SourceControllerBuilder

        super(SourceForm, self).__init__(*args, **kwargs)
        # TODO thing below should be handled by model properties
        self.fields["favicon"].required = False
        self.fields["proxy_location"].required = False

        names = SourceControllerBuilder.get_plugin_names()
        self.fields["source_type"].widget = forms.Select(choices=self.to_choices(names))

        self.fields[
            "proxy_location"
        ].help_text = "Proxy location for the source. Proxy location will be used instead of normal processing."

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
    user_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    user = forms.CharField(max_length=1000)
    tag = forms.CharField(max_length=1000)


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
            "category",
            "subcategory",
            "domain",
            "dead",
        ]

    def __init__(self, *args, **kwargs):
        super(DomainEditForm, self).__init__(*args, **kwargs)
        self.fields["domain"].widget.attrs["readonly"] = True


class DomainsChoiceForm(forms.Form):
    """
    Category choice form
    """

    search = forms.CharField(label="Search", max_length=500, required=False)
    suffix = forms.CharField(widget=forms.Select(choices=()), required=False)
    tld = forms.CharField(widget=forms.Select(choices=()), required=False)
    category = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory = forms.CharField(widget=forms.Select(choices=()), required=False)
    sort = forms.CharField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
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

        categories = self.get_categories()
        subcategories = self.get_subcategories()
        self.fields["category"].widget = forms.Select(choices=categories, attrs=attr)
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )

    def to_choices(self, names):
        names = sorted(names)
        result = []

        for name in names:
            result.append([name, name])

        return result

    def get_suffix_choices(self):
        from .models import DomainsSuffixes

        result = []
        result.append("")

        suffs = DomainsSuffixes.objects.all()
        for suff in suffs:
            if suff and suff != "":
                result.append(suff.suffix)

        return self.to_choices(result)

    def get_tld_choices(self):
        from .models import DomainsTlds

        result = []
        result.append("")

        tlds = DomainsTlds.objects.all()
        for tld in tlds:
            if tld and tld != "":
                result.append(tld.tld)

        return self.to_choices(result)

    def get_main_choices(self):
        from .models import DomainsMains

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

    def get_categories(self):
        from .models import DomainCategories

        result = []
        result.append(["", ""])

        for category in DomainCategories.objects.all():
            if category and category != "":
                result.append([category.category, category.category])

        return result

    def get_subcategories(self):
        from .models import DomainSubCategories

        result = []
        result.append(["", ""])

        for subcategory in DomainSubCategories.objects.all():
            if subcategory and subcategory != "":
                result.append([subcategory.subcategory, subcategory.subcategory])

        return result


class SourcesChoiceForm(forms.Form):
    """
    Category choice form
    """

    search = forms.CharField(label="Search", max_length=500, required=False)
    category = forms.CharField(widget=forms.Select(choices=()), required=False)
    subcategory = forms.CharField(widget=forms.Select(choices=()), required=False)

    def __init__(self, *args, **kwargs):
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
        from .models import SourceCategories

        result = []
        result.append(["", ""])

        for category in SourceCategories.objects.all():
            result.append([category.category, category.category])

        return result

    def get_subcategories(self):
        from .models import SourceSubCategories

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
        self.request = None
        self.is_mobile = False
        if "request" in kwargs:
            from .views import ViewPage

            self.request = kwargs.pop("request")
            self.is_mobile = ViewPage.is_mobile(self.request)

        super().__init__(*args, **kwargs)

    def create(self, sources):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        condition1 = Q(on_hold=False)  # & Q(proxy_location = "")
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

    def get_categories(self):
        from .models import SourceCategories

        result = []
        result.append(["", ""])

        for category in SourceCategories.objects.filter(on_hold=False):
            if category and category != "":
                result.append([category.category, category.category])

        return result

    def get_subcategories(self):
        from .models import SourceSubCategories

        result = []
        result.append(["", ""])

        for subcategory in SourceSubCategories.objects.filter(on_hold=False):
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

                if self.is_mobile:
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
    user_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    user = forms.CharField(max_length=1000)
    vote = forms.IntegerField(initial=0)

    def __init__(self, *args, **kwargs):
        super(LinkVoteForm, self).__init__(*args, **kwargs)
        self.fields["user"].readonly = True

        config = Configuration.get_object().config_entry

        self.fields["vote"].validators = [
            MaxValueValidator(config.vote_max),
            MinValueValidator(config.vote_min),
        ]
