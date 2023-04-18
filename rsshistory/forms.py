from django import forms
from .models import RssSourceDataModel, RssSourceEntryDataModel, ConfigurationEntry, RssEntryTagsDataModel, RssEntryCommentDataModel

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
        model = RssSourceDataModel
        fields = ['url', 'title', 'category', 'subcategory', 'language', 'export_to_cms', 'remove_after_days', 'favicon', 'on_hold']
        widgets = {
         #'git_token': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super(SourceForm, self).__init__(*args, **kwargs)
        self.fields['favicon'].required = False

    #def save_form(self):
    #    from .webtools import Page

    #    url = self.cleaned_data['url']
    #    favicon = self.cleaned_data['favicon']
    #    print("Utl: {0} {1}".format(url, favicon))


class EntryForm(forms.ModelForm):
    """
    Category choice form
    """
    class Meta:
        model = RssSourceEntryDataModel
        fields = ['link', 'title', 'description', 'date_published', 'source', 'persistent', 'language', 'user']
        widgets = {
         #'git_token': forms.PasswordInput(),
        }

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields['source'].required = False
        self.fields['language'].required = False
        self.fields['description'].required = False
        self.fields['title'].required = False
        self.fields['persistent'].initial = True
        self.fields['user'].widget.attrs['readonly'] = True

    def get_information(self, data):
        return self.cleaned_data

    def update_info(self, data):
        from .webtools import Page

        p = Page(data["link"])

        data["thumbnail"] = None

        if p.is_youtube():
           self.update_info_youtube(data)

        return self.update_info_default(data)

    def update_info_youtube(self, data):
        from .handlers.youtubelinkhandler import YouTubeLinkHandler
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

    def save_form(self):
        data = self.get_information(self.cleaned_data)
        data = self.update_info(data)

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
        sources = RssSourceDataModel.objects.filter(url = source)
        if sources.exists():
            source_obj = sources[0]

        links = RssSourceEntryDataModel.objects.filter(link = link)
        if len(links) > 0:
            return False

        entry = RssSourceEntryDataModel(
                source = source,
                title = title,
                description = description,
                link = link,
                date_published = date_published,
                persistent = persistent,
                thumbnail = thumbnail,
                language = language,
                user = user,
                source_obj = source_obj)

        entry.save()
        return True


class TagEntryForm(forms.ModelForm):
    """
    Category choice form
    """
    class Meta:
        model = RssEntryTagsDataModel
        fields = ['link', 'author', 'date', 'tag']
        widgets = {
         #'git_token': forms.PasswordInput(),
        }

    def save_tags(self):
        link = self.cleaned_data["link"]
        author = self.cleaned_data["author"]
        date = self.cleaned_data["date"]
        tags = self.cleaned_data["tag"]

        objs = RssEntryTagsDataModel.objects.filter(author = author, link = link)
        if objs.exists():
            objs.delete()

        tags_set = set()
        tags = tags.split(RssEntryTagsDataModel.get_delim())
        for tag in tags:
            tag = str(tag).strip()
            tag = tag.lower()
            if tag != "":
                tags_set.add(tag)

        link_objs = RssSourceEntryDataModel.objects.filter(link = link)

        for tag in tags_set:
            model = RssEntryTagsDataModel(link = link, author = author, date = date, tag = tag, link_obj = link_objs[0])
            model.save()


class TagRenameForm(forms.Form):
    """
    Category choice form
    """
    current_tag = forms.CharField(label='Current tag', max_length = 100)
    new_tag = forms.CharField(label='New tag', max_length = 100)


class ImportSourcesForm(forms.Form):
    """
    Import links form
    """
    rawsources = forms.CharField(widget=forms.Textarea(attrs={'name':'rawsources', 'rows':30, 'cols':100}))

    def get_sources(self):
        from .serializers.converters import CsvConverter
        rawsources = self.cleaned_data['rawsources']

        converter = CsvConverter()
        return converter.from_text(rawsources)


class ImportEntriesForm(forms.Form):
    """
    Import links form
    """
    rawentries = forms.CharField(widget=forms.Textarea(attrs={'name':'rawentries', 'rows':30, 'cols':100}))

    def get_entries(self):
        from .serializers.converters import CsvConverter
        rawentries = self.cleaned_data['rawentries']

        converter = CsvConverter()
        return converter.from_text(rawsources)


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
        self.filtered_objects = RssSourceDataModel.objects.filter(**parameter_map)
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

    # do not think too much about these settings, these will be overriden by 'create' method
    search = forms.CharField(label='Search', max_length = 500, required=False)
    category = forms.CharField(widget=forms.Select(choices=()))
    subcategory = forms.CharField(widget=forms.Select(choices=()))
    title = forms.CharField(widget=forms.Select(choices=()))
    persistent = forms.BooleanField(required=False, initial=False)
    language = forms.CharField(label='language', max_length = 500, required=False)
    user = forms.CharField(label='user', max_length = 500, required=False)
    tag = forms.CharField(label='tag', max_length = 500, required=False)

    def __init__(self, *args, **kwargs):
        self.args = kwargs.pop('args', ())
        super().__init__(*args, **kwargs)

    def get_filtered_objects(self):
        source_parameter_map = self.get_source_filter_args()
        entry_parameter_map = self.get_entry_filter_args(False)

        self.entries = []
        self.entries = RssSourceEntryDataModel.objects.filter(**entry_parameter_map)

        return self.entries

    def create(self):
        # how to unpack dynamic forms
        # https://stackoverflow.com/questions/60393884/how-to-pass-choices-dynamically-into-a-django-form

        self.get_sources()

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

        init = {}
        init['search'] = ""
        init['language'] = ""
        init['persistent'] = False
        init['user'] = ""
        init['tag'] = ""
        if len(self.args) != 0:
            init['search'] = self.args.get("search")
            init['language'] = self.args.get("language")
            init['persistent'] = self.args.get("persistent")
            init['user'] = self.args.get("user")
            init['tag'] = self.args.get("tag")

        self.fields['search'] = forms.CharField(label = 'Search', max_length = 500, required=False, initial=init['search'])
        self.fields['category'] = forms.CharField(label = "RSS source category", widget=forms.Select(choices=categories, attrs=attr), initial=category_init)
        self.fields['subcategory'] = forms.CharField(label = "RSS source subcategory", widget=forms.Select(choices=subcategories, attrs=attr), initial=subcategory_init)
        self.fields['title'] = forms.CharField(label = "RSS source title", widget=forms.Select(choices=title, attrs=attr), initial=title_init)
        self.fields['persistent'] = forms.BooleanField(label = "Search in bookmarked entries", required=False, initial=init['persistent'])
        self.fields['language'] = forms.CharField(label = 'Search language', max_length = 500, required=False, initial=init['language'])
        self.fields['user'] = forms.CharField(label = 'Search user', required=False, initial=init['user'])
        self.fields['tag'] = forms.CharField(label = 'Search tags', required=False, initial=init['tag'])

    def get_sources(self):
        source_parameter_map = self.get_source_filter_args()
        self.sources = RssSourceDataModel.objects.filter(**source_parameter_map)

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

    def get_entry_filter_args(self, pure_data = True):
        parameter_map = {}

        persistent = self.args.get("persistent")
        if persistent:
           parameter_map['persistent'] = True
        #else:
        #   parameter_map['persistent'] = False

        search = self.args.get("search")
        language = self.args.get("language")
        user = self.args.get("user")

        tag = self.args.get("tag")

        category = self.args.get("category")
        subcategory = self.args.get("subcategory")
        source_title = self.args.get("title")

        if pure_data:
            if search:
               parameter_map['search'] = search
            if language:
               parameter_map['language'] = language
            if user:
               parameter_map['user'] = user
            if tag:
               parameter_map['tag'] = tag

        else:
            tag_key, tag = self.get_tag_search()

            if search:
                parameter_map["title__icontains"] = search
            if language:
                parameter_map["language__icontains"] = language
            if user:
                parameter_map["user"] = user
            if tag:
               parameter_map[tag_key] = tag
            if category and category != "Any":
               parameter_map['source_obj__category'] = category
            if subcategory and subcategory != "Any":
               parameter_map['source_obj__subcategory'] = subcategory
            if source_title and source_title != "Any":
               parameter_map['source_obj__title'] = source_title

        return parameter_map

    def get_tag_search(self):
        tag = self.args.get("tag")
        if tag is None:
            return None, None

        tag_find_exact, tag = self.get_search_keyword(tag)
        if tag_find_exact:
            key = 'tags__tag'
        else:
            key = 'tags__tag__icontains'
        return key, tag

    def get_search_keyword(self, text):
        exact_find = False
        if text.find('"') >= 0:
            text = text[1:-1]
            exact_find = True
        return exact_find, text

    def get_filter_string(self):
        filters = self.get_source_filter_args()
        filters.update(self.get_entry_filter_args())

        if "cagetory" in filters and filters["category"] == "Any":
            del filters["category"]
        if "subcagetory" in filters and filters["subcategory"] == "Any":
            del filters["subcategory"]
        if "title" in filters and filters["title"] == "Any":
            del filters["title"]

        for filter_name in filters:
            filtervalue = filters[filter_name]
            if filtervalue and str(filtervalue).strip() == "":
                del filters[filter_name]

        filter_string = ""
        for key in filters:
            filter_string += "&{0}={1}".format(key, filters[key])

        return filter_string


class GoogleChoiceForm(forms.Form):
    """
    Category choice form
    """

    category = forms.CharField(widget=forms.Select(choices=()))
    subcategory = forms.CharField(widget=forms.Select(choices=()))
    title = forms.CharField(widget=forms.Select(choices=()))
    persistent = forms.BooleanField(required=False)
    search = forms.CharField(label='Search', max_length = 500, required=False)


class ConfigForm(forms.ModelForm):
    """
    Category choice form
    """
    class Meta:
        model = ConfigurationEntry
        fields = ['git_path', 'git_repo', 'git_daily_repo', 'git_user', 'git_token']
        widgets = {
         #'git_token': forms.PasswordInput(),
        }


class ImportSourceFromInternetArchiveForm(forms.Form):
    source_url = forms.CharField(label='Source url', max_length = 500)
    archive_time = forms.DateField(label = "Archive time")


class ImportSourceRangeFromInternetArchiveForm(forms.Form):
    source_url = forms.CharField(label='Source url', max_length = 500)
    archive_start = forms.DateField(label = "Start time")
    archive_stop = forms.DateField(label = "Stop time")


from .models import RssEntryCommentDataModel

class CommentEntryForm(forms.ModelForm):
    """
    Category choice form
    """
    class Meta:
        model = RssEntryCommentDataModel
        fields = ['comment', 'link', 'date_published', 'author']

    def __init__(self, *args, **kwargs):
        super(CommentEntryForm, self).__init__(*args, **kwargs)
        self.fields['link'].widget.attrs['readonly'] = True
        self.fields['author'].widget.attrs['readonly'] = True

    def save_comment(self):
        comment = self.cleaned_data['comment']
        link_url = self.cleaned_data['link']
        date_published = self.cleaned_data['date_published']
        author = self.cleaned_data['author']

        entry = RssSourceEntryDataModel.objects.get(link = link_url)

        o = RssEntryCommentDataModel(
                comment = comment,
                link = link_url,
                author = author,
                date_published = date_published,
                link_obj = entry)
        o.save()


class YouTubeLinkSimpleForm(forms.Form):
    """
    Import links form
    """
    youtube_link = forms.CharField(label='YouTube Link URL', max_length = 500)
