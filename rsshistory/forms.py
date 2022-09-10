from django import forms
from .models import RssLinkDataModel, RssLinkEntryDataModel, ConfigurationEntry
from .models import SourcesConverter, EntriesConverter

# https://docs.djangoproject.com/en/4.1/ref/forms/widgets/

#class NewLinkForm(forms.Form):
#    """
#    New link form
#    """
#    class Meta:
#        model = LinkDataModel
#        fields = ['url', 'category', 'subcategory', 'artist', 'album', 'title', 'date_created']


class SourceForm(forms.ModelForm):
    """
    Category choice form
    """
    class Meta:
        model = RssLinkDataModel
        fields = ['url', 'title', 'category', 'subcategory', 'date_fetched']
        widgets = {
         #'git_token': forms.PasswordInput(),
        }


class EntryForm(forms.ModelForm):
    """
    Category choice form
    """
    class Meta:
        model = RssLinkEntryDataModel
        fields = ['url', 'title', 'description', 'link', 'date_published', 'favourite']
        widgets = {
         #'git_token': forms.PasswordInput(),
        }


class ImportSourcesForm(forms.Form):
    """
    Import links form
    """
    rawsources = forms.CharField(widget=forms.Textarea(attrs={'name':'rawsources', 'rows':30, 'cols':100}))

    def get_sources(self):
        rawsources = self.cleaned_data['rawsources']
        sources = SourcesConverter(rawsources)
        return sources.sources


class ImportEntriesForm(forms.Form):
    """
    Import links form
    """
    rawentries = forms.CharField(widget=forms.Textarea(attrs={'name':'rawentries', 'rows':30, 'cols':100}))

    def get_entries(self):
        rawentries = self.cleaned_data['rawentries']
        entries = EntriesConverter(rawentries)
        return entries.entries


class SourcesChoiceForm(forms.Form):
    """
    Category choice form
    """

    category = forms.CharField(widget=forms.Select(choices=()))
    subcategory = forms.CharField(widget=forms.Select(choices=()))
    title = forms.CharField(widget=forms.Select(choices=()))

    def __init__(self, *args, **kwargs):
        self.args = kwargs.pop('args', ())
        super().__init__(*args, **kwargs)

    def get_filtered_objects(self):
        parameter_map = self.get_filter_args()
        self.filtered_objects = RssLinkDataModel.objects.filter(**parameter_map)
        return self.filtered_objects

    def create(self):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        categories = self.get_filtered_objects_values('category')
        subcategories = self.get_filtered_objects_values('subcategory')
        title = self.get_filtered_objects_values('title')

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange" : "this.form.submit()"}

        # default form value
        # https://stackoverflow.com/questions/604266/django-set-default-form-values
        category_init = self.get_init('category')
        subcategory_init = self.get_init('subcategory')
        title_init = self.get_init('title')

        self.fields['category'] = forms.CharField(widget=forms.Select(choices=categories, attrs=attr), initial=category_init)
        self.fields['subcategory'] = forms.CharField(widget=forms.Select(choices=subcategories, attrs=attr), initial=subcategory_init)
        self.fields['title'] = forms.CharField(widget=forms.Select(choices=title, attrs=attr), initial=title_init)

    def get_init(self, column):
        filters = self.get_filter_args()
        if column in filters:
            return filters[column]
        else:
            return "Any"

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
                result.append((item, item))
        return result

    def get_filter_args(self):
        parameter_map = {}

        category = self.args.get("category")
        if category and category != "Any":
           parameter_map['category'] = category

        subcategory = self.args.get("subcategory")
        if subcategory and subcategory != "Any":
           parameter_map['subcategory'] = subcategory

        title = self.args.get("title")
        if title and title != "Any":
           parameter_map['title'] = title

        return parameter_map


class EntryChoiceForm(forms.Form):
    """
    Category choice form
    """

    category = forms.CharField(widget=forms.Select(choices=()))
    subcategory = forms.CharField(widget=forms.Select(choices=()))
    title = forms.CharField(widget=forms.Select(choices=()))
    favourite = forms.BooleanField(required=False)
    search = forms.CharField(label='Search', max_length = 500, required=False)

    def __init__(self, *args, **kwargs):
        self.args = kwargs.pop('args', ())
        super().__init__(*args, **kwargs)

    def get_filtered_objects(self):
        source_parameter_map = self.get_source_filter_args()
        entry_parameter_map = self.get_entry_filter_args()

        if 'search' in entry_parameter_map:
            print("parameters: " + entry_parameter_map['search'])
            entry_parameter_map["title__icontains"] = entry_parameter_map['search']
            del entry_parameter_map['search']

        self.entries = []
        self.sources = RssLinkDataModel.objects.filter(**source_parameter_map)

        if source_parameter_map == {}:
            return RssLinkEntryDataModel.objects.filter(**entry_parameter_map)

        if self.sources.exists():
            index = 0
            for obj in self.sources:
                entry_parameter_map["url"] = obj.url

                if index == 0:
                    self.entries = RssLinkEntryDataModel.objects.filter(**entry_parameter_map)
                else:
                    self.entries = self.entries | RssLinkEntryDataModel.objects.filter(**entry_parameter_map)
                index += 1
        else:
            self.entries = RssLinkEntryDataModel.objects.filter(**entry_parameter_map)

        return self.entries

    def create(self):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        categories = self.get_filtered_objects_values('category')
        subcategories = self.get_filtered_objects_values('subcategory')
        title = self.get_filtered_objects_values('title')

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange" : "this.form.submit()"}

        # default form value
        # https://stackoverflow.com/questions/604266/django-set-default-form-values
        category_init = self.get_source_init('category')
        subcategory_init = self.get_source_init('subcategory')
        title_init = self.get_source_init('title')

        self.fields['category'] = forms.CharField(widget=forms.Select(choices=categories, attrs=attr), initial=category_init)
        self.fields['subcategory'] = forms.CharField(widget=forms.Select(choices=subcategories, attrs=attr), initial=subcategory_init)
        self.fields['title'] = forms.CharField(widget=forms.Select(choices=title, attrs=attr), initial=title_init)
        self.fields['favourite'] = forms.BooleanField(required=False, initial=self.args.get('favourite'))
        self.fields['search'] = forms.CharField(label='Search', max_length = 500, required=False, initial=self.args.get("search"))

    def get_filtered_objects_values(self, field):
        values = set()
        values.add("Any")

        for val in self.sources.values(field):
            if str(val).strip() != "":
                values.add(val[field])

        dict_values = self.to_dict(values)

        return dict_values

    def get_source_init(self, column):
        filters = self.get_source_filter_args()
        if column in filters:
            return filters[column]
        else:
            return "Any"

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
            if item.strip() != "":
                result.append((item, item))
        return result

    def get_source_filter_args(self):
        parameter_map = {}

        category = self.args.get("category")
        if category and category != "Any":
           parameter_map['category'] = category

        subcategory = self.args.get("subcategory")
        if subcategory and subcategory != "Any":
           parameter_map['subcategory'] = subcategory

        title = self.args.get("title")
        if title and title != "Any":
           parameter_map['title'] = title

        return parameter_map

    def get_entry_filter_args(self):
        parameter_map = {}

        favourite = self.args.get("favourite")
        if favourite:
           parameter_map['favourite'] = True

        search = self.args.get("search")
        if search:
           parameter_map['search'] = search

        return parameter_map


class ConfigForm(forms.ModelForm):
    """
    Category choice form
    """
    class Meta:
        model = ConfigurationEntry
        fields = ['git_path', 'git_repo', 'git_user', 'git_token']
        widgets = {
         #'git_token': forms.PasswordInput(),
        }
