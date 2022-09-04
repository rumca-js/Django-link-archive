from django import forms
from .models import RssLinkDataModel

# https://docs.djangoproject.com/en/4.1/ref/forms/widgets/

#class NewLinkForm(forms.Form):
#    """
#    New link form
#    """
#    class Meta:
#        model = LinkDataModel
#        fields = ['url', 'category', 'subcategory', 'artist', 'album', 'title', 'date_created']


class NewLinkForm(forms.Form):
    """
    New link form
    """
    url = forms.CharField(label='Url', max_length = 500)
    category = forms.CharField(label='Category', max_length = 100)
    subcategory = forms.CharField(label='Subcategory', max_length = 100)
    title = forms.CharField(label='Title', max_length = 200)

    class Meta:
        model = RssLinkDataModel

    def __init__(self, *args, **kwargs):
        init_obj = kwargs.pop('init_obj', ())

        super().__init__(*args, **kwargs)

        if init_obj != ():
            self.fields['url'] = forms.CharField(label='Url', max_length = 500, initial=init_obj.url)
            self.fields['category'] = forms.CharField(label='Category', max_length = 100, initial=init_obj.category)
            self.fields['subcategory'] = forms.CharField(label='Subcategory', max_length = 100, initial=init_obj.subcategory)
            self.fields['title'] = forms.CharField(label='Title', max_length = 100, initial=init_obj.title)
        else:
            from django.utils.timezone import now

    def to_model(self):
        url = self.cleaned_data['url']
        category = self.cleaned_data['category']
        subcategory = self.cleaned_data['subcategory']
        title = self.cleaned_data['title']

        record = RssLinkDataModel(url=url,
                                    title=title,
                                    category=category,
                                    subcategory=subcategory)

        return record


class ImportLinksForm(forms.Form):
    """
    Import links form
    """
    rawlinks = forms.CharField(widget=forms.Textarea(attrs={'name':'rawlinks', 'rows':30, 'cols':100}))


class SourcesChoiceForm(forms.Form):
    """
    Category choice form
    """

    category = forms.CharField(widget=forms.Select(choices=()))
    subcategory = forms.CharField(widget=forms.Select(choices=()))
    title = forms.CharField(widget=forms.Select(choices=()))

    def __init__(self, *args, **kwargs):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        categories = kwargs.pop('categories', ())
        subcategories = kwargs.pop('subcategories', ())
        title = kwargs.pop('title', ())
        filters = kwargs.pop('filters', ())

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange" : "this.form.submit()"}

        # default form value
        # https://stackoverflow.com/questions/604266/django-set-default-form-values
        category_init = 'Any'
        if 'category' in filters:
            category_init = filters['category']
        subcategory_init = 'Any'
        if 'subcategory' in filters:
            subcategory_init = filters['subcategory']
        title_init = 'Any'
        if 'title' in filters:
            title_init = filters['title']

        super().__init__(*args, **kwargs)

        self.fields['category'] = forms.CharField(widget=forms.Select(choices=categories, attrs=attr), initial=category_init)
        self.fields['subcategory'] = forms.CharField(widget=forms.Select(choices=subcategories, attrs=attr), initial=subcategory_init)
        self.fields['title'] = forms.CharField(widget=forms.Select(choices=title, attrs=attr), initial=title_init)


class EntryChoiceForm(forms.Form):
    """
    Category choice form
    """

    category = forms.CharField(widget=forms.Select(choices=()))
    subcategory = forms.CharField(widget=forms.Select(choices=()))
    title = forms.CharField(widget=forms.Select(choices=()))
    favourite = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form
        request_get_args = kwargs.pop('request_get_args', ())
        self.entry_query_set = kwargs.pop('entry_query_set', ())
        self.sources_query_set = kwargs.pop('sources_query_set', ())

        #categories = kwargs.pop('categories', ())
        #subcategories = kwargs.pop('subcategories', ())
        #title = kwargs.pop('title', ())
        filters = EntryChoiceForm.get_source_filter_args(request_get_args)

        categories = self.get_request_values('category')
        subcategories = self.get_request_values('subcategory')
        title = self.get_request_values('title')

        categories = self.to_dict(categories)
        subcategories = self.to_dict(subcategories)
        title = self.to_dict(title)

        # custom javascript code
        # https://stackoverflow.com/questions/10099710/how-to-manually-create-a-select-field-from-a-modelform-in-django
        attr = {"onchange" : "this.form.submit()"}

        # default form value
        # https://stackoverflow.com/questions/604266/django-set-default-form-values
        category_init = 'Any'
        if 'category' in filters:
            category_init = filters['category']
        subcategory_init = 'Any'
        if 'subcategory' in filters:
            subcategory_init = filters['subcategory']
        title_init = 'Any'
        if 'title' in filters:
            title_init = filters['title']

        super().__init__(*args, **kwargs)

        self.fields['category'] = forms.CharField(widget=forms.Select(choices=categories, attrs=attr), initial=category_init)
        self.fields['subcategory'] = forms.CharField(widget=forms.Select(choices=subcategories, attrs=attr), initial=subcategory_init)
        self.fields['title'] = forms.CharField(widget=forms.Select(choices=title, attrs=attr), initial=title_init)

    def get_request_values(self, field):
        values = set()
        values.add("Any")
        for val in self.sources_query_set.values(field):
            if str(val).strip() != "":
                values.add(val[field])

        return values

    def to_dict(self, alist):
        result = []
        for item in sorted(alist):
            if item.strip() != "":
                result.append((item, item))
        return result

    def get_source_filter_args(get_args):
        parameter_map = {}

        category = get_args.get("category")
        if category and category != "Any":
           parameter_map['category'] = category

        subcategory = get_args.get("subcategory")
        if subcategory and subcategory != "Any":
           parameter_map['subcategory'] = subcategory

        title = get_args.get("title")
        if title and title != "Any":
           parameter_map['title'] = title

        return parameter_map

    def get_entry_filter_args(get_args):
        parameter_map = {}

        favourite = get_args.get("favourite")
        if favourite:
           parameter_map['favourite'] = True

        return parameter_map
