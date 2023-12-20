from datetime import datetime, timedelta, date
from django import forms

from .models import (
    BackgroundJob,
    LinkTagsDataModel,
    LinkCommentDataModel,
    LinkVoteDataModel,
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
            "user_agent",
            "sources_refresh_period",
            "access_type",
            # optional
            "link_save",
            "source_save",
            "auto_store_entries",
            "auto_store_sources",
            "auto_store_sources_enabled",
            "auto_store_domain_info",
            "auto_store_keyword_info",
            "track_user_actions",
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
        ]

    def __init__(self, *args, **kwargs):
        super(ConfigForm, self).__init__(*args, **kwargs)


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


class UserConfigForm(forms.ModelForm):
    """
    Category choice form
    """

    class Meta:
        model = UserConfig
        fields = [
            "show_icons",
            "thumbnails_as_icons",
            "small_icons",
            "display_type",
            "display_style",
        ]
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


class ExportTopicForm(forms.Form):
    tag = forms.CharField(label="Tag", max_length=500)
    store_domain_info = forms.BooleanField()


class TagForm(forms.Form):
    """
    Import links form
    """

    tag = forms.CharField(label="Tag name", max_length=500)


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


class OmniSearchWithArchiveForm(OmniSearchForm):
    """
    Import links form
    """

    archive = forms.BooleanField(label="Search archive", required=False)


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
        fields = ["link", "author", "tag"]
        widgets = {
            #    'date': forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'})
        }


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
    source_title = forms.CharField(widget=forms.Select(choices=()), required=False)

    def create(self, sources):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        self.sources = SourceDataController.objects.filter(on_hold=False)

        categories = self.get_sources_values("category")
        subcategories = self.get_sources_values("subcategory")
        title = self.get_sources_values("title")

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange": "this.form.submit()"}

        self.fields["category"].widget = forms.Select(choices=categories, attrs=attr)
        self.fields["subcategory"].widget = forms.Select(
            choices=subcategories, attrs=attr
        )
        self.fields["source_title"].widget = forms.Select(choices=title, attrs=attr)

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

    link_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    author = forms.CharField(
        max_length=1000, widget=forms.TextInput(attrs={"readonly": "readonly"})
    )
    comment = forms.CharField(widget=forms.Textarea)
    date_published = forms.DateTimeField(
        initial=datetime.now,
        widget=forms.widgets.DateTimeInput(
            attrs={"type": "datetime-local", "readonly": "readonly"}
        ),
    )


from django.db.models import IntegerField, Model
from django.core.validators import MaxValueValidator, MinValueValidator


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

        config = Configuration.get_object().config_entry

        self.fields["vote"].validators = [
            MaxValueValidator(config.vote_max),
            MinValueValidator(config.vote_min),
        ]
