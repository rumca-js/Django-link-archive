
from django.views import generic
from django.urls import reverse
from django.shortcuts import render

from ..models import SourceDataModel, LinkDataModel, BackgroundJob
from ..prjconfig import Configuration
from ..forms import SourceForm, ImportSourcesForm, SourcesChoiceForm, ConfigForm


def init_context(request, context):
    from ..views import init_context
    return init_context(request, context)

def get_context(request):
    from ..views import get_context
    return get_context(request)

def get_app():
    from ..views import app_name
    return app_name


class RssSourceListView(generic.ListView):
    model = SourceDataModel
    context_object_name = 'source_list'
    paginate_by = 100

    def get_queryset(self):

        self.filter_form = SourcesChoiceForm(args = self.request.GET)
        return self.filter_form.get_filtered_objects()

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super(RssSourceListView, self).get_context_data(**kwargs)
        context = init_context(self.request, context)
        # Create any data and add it to the context

        self.filter_form.create()
        self.filter_form.method = "GET"
        self.filter_form.action_url = reverse('rsshistory:sources')

        context['filter_form'] = self.filter_form
        context['page_title'] += " - news source list"

        from django_user_agents.utils import get_user_agent
        user_agent = get_user_agent(self.request)
        context["is_mobile"] = user_agent.is_mobile

        return context


class RssSourceDetailView(generic.DetailView):
    model = SourceDataModel

    def get_context_data(self, **kwargs):
        from ..handlers.sourcecontroller import SourceController
        # Call the base implementation first to get the context
        context = super(RssSourceDetailView, self).get_context_data(**kwargs)
        context = init_context(self.request, context)

        context['page_title'] = self.object.title
        context['handler'] = SourceController(self.object)

        return context


def add_source(request):
    context = get_context(request)
    context['page_title'] += " - add source"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = SourceForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            form.save()

            context["summary_text"] = "Source added"
            return render(request, get_app() / 'summary_present.html', context)
        else:
            context["summary_text"] = "Source not added"
            return render(request, get_app() / 'summary_present.html', context)

        #    # process the data in form.cleaned_data as required
        #    # ...
        #    # redirect to a new URL:
        #    #return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = SourceForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:source-add')
        context['form'] = form

        context['form_title'] = "Add new source"

        form_text = "<pre>"
        form_text += " - Specify all fields, if possible\n"
        form_text += " - if favicon is not specified, it is set to domain/favicon.ico\n"
        form_text += "</pre>"

        context['form_description_post'] = form_text

    return render(request, get_app() / 'form_basic.html', context)


def edit_source(request, pk):
    context = get_context(request)
    context['page_title'] += " - edit source"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, get_app() / 'source_edit_does_not_exist.html', context)

    ob = ft[0]

    if request.method == 'POST':
        form = SourceForm(request.POST, instance=ob)
        context['form'] = form

        if form.is_valid():
            form.save()

            context['source'] = ob
            return render(request, get_app() / 'source_edit_ok.html', context)

        context['summary_text'] = "Could not edit source"

        return render(request, get_app() / 'summary_present.html', context)
    else:
        if not ob.favicon:
            from ..webtools import Page
            p = Page(ob.url)

            form = SourceForm(instance=ob, initial={'favicon' : p.get_domain() +"/favicon.ico" })
        else:
            form = SourceForm(instance=ob)

        form.method = "POST"
        form.action_url = reverse('rsshistory:source-edit', args=[pk])
        context['form'] = form
        return render(request, get_app() / 'form_basic.html', context)


def refresh_source(request, pk):
    from ..models import SourceOperationalData

    context = get_context(request)
    context['page_title'] += " - refresh source"
    context['pk'] = pk

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.filter(id=pk)
    if not ft.exists():
       return render(request, get_app() / 'source_edit_does_not_exist.html', context)

    ob = ft[0]

    operational = SourceOperationalData.objects.filter(url = ob.url)
    if operational.exists():
        op = operational[0]
        op.date_fetched = None
        op.save()

    c = Configuration.get_object(str(get_app()))
    if not c.thread_mgr:
        context['summary_text'] = "Source added, but could not add to queue - missing threads"
        return render(request, get_app() / 'summary_present.html', context)

    BackgroundJob.download_rss(ob, True)

    context['summary_text'] = "Source added to refresh queue"
    return render(request, get_app() / 'summary_present.html', context)


def import_sources(request):
    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import sources"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        method = "POST"

        # create a form instance and populate it with data from the request:
        form = ImportSourcesForm(request.POST)

        if form.is_valid():
            for source in form.get_sources():

                if SourceDataModel.objects.filter(url=source.url).exists():
                    summary_text += source.title + " " + source.url + " " + " Error: Already present in db\n"
                else:
                    record = SourceDataModel(url=source.url,
                                                title=source.title,
                                                category=source.category,
                                                subcategory=source.subcategory)
                    record.save()
                    summary_text += source.title + " " + source.url + " " + " OK\n"
        else:
            summary_text = "Form is invalid"

        context["form"] = form
        context['summary_text'] = summary_text
        return render(request, get_app() / 'sources_import_summary.html', context)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ImportSourcesForm()
        form.method = "POST"
        form.action_url = reverse('rsshistory:sources-import')
        context["form"] = form
        return render(request, get_app() / 'form_basic.html', context)


def remove_source(request, pk):
    context = get_context(request)
    context['page_title'] += " - remove source"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.filter(id=pk)
    if ft.exists():
        source_url = ft[0].url
        ft.delete()
        
        # TODO checkbox - or other button to remove corresponding entries
        #entries = LinkDataModel.objects.filter(url = source_url)
        #if entries.exists():
        #    entries.delete()

        context["summary_text"] = "Remove ok"
    else:
        context["summary_text"] = "No source for ID: " + str(pk)

    return render(request, get_app() / 'summary_present.html', context)


def remove_all_sources(request):
    context = get_context(request)
    context['page_title'] += " - remove all links"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    ft = SourceDataModel.objects.all()
    if ft.exists():
        ft.delete()
        context["summary_text"] = "Removing all sources ok"
    else:
        context["summary_text"] = "No source to remove"

    return render(request, get_app() / 'summary_present.html', context)


def wayback_save(request, pk):
    context = get_context(request)
    context['page_title'] += " - Waybacksave"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    if ConfigurationEntry.get().source_archive:
        source = SourceDataModel.objects.get(id=pk)
        BackgroundJob.link_archive(subject=source.url)

        context["summary_text"] = "Added to waybacksave"
    else:
        context["summary_text"] = "Waybacksave is disabled for sources"

    return render(request, get_app() / 'summary_present.html', context)


def process_source_text(request, pk):
    context = get_context(request)
    context['page_title'] += " - process"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    text = """
    <!doctype html><html lang="en" dir="ltr"><head><meta charSet="utf-8"/><title>The Joe Rogan Experience | Video Podcast on Spotify</title><meta property="og:site_name" content="Spotify"/><meta property="fb:app_id" content="174829003346"/><link rel="icon" sizes="32x32" type="image/png" href="https://open.spotifycdn.com/cdn/images/favicon32.b64ecc03.png"/><link rel="icon" sizes="16x16" type="image/png" href="https://open.spotifycdn.com/cdn/images/favicon16.1c487bff.png"/><link rel="icon" href="https://open.spotifycdn.com/cdn/images/favicon.0f31d2ea.ico"/><meta http-equiv="X-UA-Compatible" content="IE=9"/><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1"/><link rel="preload" href="https://encore.scdn.co/fonts/CircularSp-Book-4eaffdf96f4c6f984686e93d5d9cb325.woff2" as="font" type="font/woff2" crossorigin="anonymous"/><link rel="preload" href="https://encore.scdn.co/fonts/CircularSp-Bold-fe1cfc14b7498b187c78fa72fb72d148.woff2" as="font" type="font/woff2" crossorigin="anonymous"/><link rel="preload" href="https://encore.scdn.co/fonts/CircularSpTitle-Bold-2fbf72b606d7f0b0f771ea4956a8b4d6.woff2" as="font" type="font/woff2" crossorigin="anonymous"/><link rel="preload" href="https://encore.scdn.co/fonts/CircularSpTitle-Black-3f9afb402080d53345ca1850226ca724.woff2" as="font" type="font/woff2" crossorigin="anonymous"/><link rel="preload" href="https://open.spotifycdn.com/cdn/fonts/spoticon_regular_2.d728648c.woff2" as="font" type="font/woff2" crossorigin="anonymous"/><meta name="description" content="Listen to The Joe Rogan Experience on Spotify. The official podcast of comedian Joe Rogan. Follow The Joe Rogan Clips show page for some of the best moments from the episodes."/><meta name="google" content="notranslate"/><meta property="og:title" content="The Joe Rogan Experience"/><meta property="og:description" content="Listen to The Joe Rogan Experience on Spotify. The official podcast of comedian Joe Rogan. Follow The Joe Rogan Clips show page for some of the best moments from the episodes."/><meta property="og:url" content="https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk"/><meta property="og:image" content="https://i.scdn.co/image/9af79fd06e34dea3cd27c4e1cd6ec7343ce20af4"/><meta property="og:type" content="website"/><meta property="og:site_name" content="Spotify"/><meta property="og:restrictions:country:allowed" content="AD"/><meta property="og:restrictions:country:allowed" content="AE"/><meta property="og:restrictions:country:allowed" content="AG"/><meta property="og:restrictions:country:allowed" content="AL"/><meta property="og:restrictions:country:allowed" content="AM"/><meta property="og:restrictions:country:allowed" content="AO"/><meta property="og:restrictions:country:allowed" content="AR"/><meta property="og:restrictions:country:allowed" content="AT"/><meta property="og:restrictions:country:allowed" content="AU"/><meta property="og:restrictions:country:allowed" content="AZ"/><meta property="og:restrictions:country:allowed" content="BA"/><meta property="og:restrictions:country:allowed" content="BB"/><meta property="og:restrictions:country:allowed" content="BE"/><meta property="og:restrictions:country:allowed" content="BF"/><meta property="og:restrictions:country:allowed" content="BG"/><meta property="og:restrictions:country:allowed" content="BH"/><meta property="og:restrictions:country:allowed" content="BI"/><meta property="og:restrictions:country:allowed" content="BJ"/><meta property="og:restrictions:country:allowed" content="BN"/><meta property="og:restrictions:country:allowed" content="BO"/><meta property="og:restrictions:country:allowed" content="BR"/><meta property="og:restrictions:country:allowed" content="BS"/><meta property="og:restrictions:country:allowed" content="BT"/><meta property="og:restrictions:country:allowed" content="BW"/><meta property="og:restrictions:country:allowed" content="BZ"/><meta property="og:restrictions:country:allowed" content="CA"/><meta property="og:restrictions:country:allowed" content="CH"/><meta property="og:restrictions:country:allowed" content="CI"/><meta property="og:restrictions:country:allowed" content="CL"/><meta property="og:restrictions:country:allowed" content="CM"/><meta property="og:restrictions:country:allowed" content="CO"/><meta property="og:restrictions:country:allowed" content="CR"/><meta property="og:restrictions:country:allowed" content="CV"/><meta property="og:restrictions:country:allowed" content="CW"/><meta property="og:restrictions:country:allowed" content="CY"/><meta property="og:restrictions:country:allowed" content="CZ"/><meta property="og:restrictions:country:allowed" content="DE"/><meta property="og:restrictions:country:allowed" content="DJ"/><meta property="og:restrictions:country:allowed" content="DK"/><meta property="og:restrictions:country:allowed" content="DM"/><meta property="og:restrictions:country:allowed" content="DO"/><meta property="og:restrictions:country:allowed" content="DZ"/><meta property="og:restrictions:country:allowed" content="EC"/><meta property="og:restrictions:country:allowed" content="EE"/><meta property="og:restrictions:country:allowed" content="EG"/><meta property="og:restrictions:country:allowed" content="ES"/><meta property="og:restrictions:country:allowed" content="FI"/><meta property="og:restrictions:country:allowed" content="FJ"/><meta property="og:restrictions:country:allowed" content="FM"/><meta property="og:restrictions:country:allowed" content="FR"/><meta property="og:restrictions:country:allowed" content="GA"/><meta property="og:restrictions:country:allowed" content="GB"/><meta property="og:restrictions:country:allowed" content="GD"/><meta property="og:restrictions:country:allowed" content="GE"/><meta property="og:restrictions:country:allowed" content="GH"/><meta property="og:restrictions:country:allowed" content="GM"/><meta property="og:restrictions:country:allowed" content="GN"/><meta property="og:restrictions:country:allowed" content="GQ"/><meta property="og:restrictions:country:allowed" content="GR"/><meta property="og:restrictions:country:allowed" content="GT"/><meta property="og:restrictions:country:allowed" content="GW"/><meta property="og:restrictions:country:allowed" content="GY"/><meta property="og:restrictions:country:allowed" content="HK"/><meta property="og:restrictions:country:allowed" content="HN"/><meta property="og:restrictions:country:allowed" content="HR"/><meta property="og:restrictions:country:allowed" content="HT"/><meta property="og:restrictions:country:allowed" content="HU"/><meta property="og:restrictions:country:allowed" content="ID"/><meta property="og:restrictions:country:allowed" content="IE"/><meta property="og:restrictions:country:allowed" content="IL"/><meta property="og:restrictions:country:allowed" content="IN"/><meta property="og:restrictions:country:allowed" content="IS"/><meta property="og:restrictions:country:allowed" content="IT"/><meta property="og:restrictions:country:allowed" content="JM"/><meta property="og:restrictions:country:allowed" content="JO"/><meta property="og:restrictions:country:allowed" content="JP"/><meta property="og:restrictions:country:allowed" content="KE"/><meta property="og:restrictions:country:allowed" content="KH"/><meta property="og:restrictions:country:allowed" content="KI"/><meta property="og:restrictions:country:allowed" content="KM"/><meta property="og:restrictions:country:allowed" content="KN"/><meta property="og:restrictions:country:allowed" content="KR"/><meta property="og:restrictions:country:allowed" content="KW"/><meta property="og:restrictions:country:allowed" content="LA"/><meta property="og:restrictions:country:allowed" content="LB"/><meta property="og:restrictions:country:allowed" content="LC"/><meta property="og:restrictions:country:allowed" content="LI"/><meta property="og:restrictions:country:allowed" content="LR"/><meta property="og:restrictions:country:allowed" content="LS"/><meta property="og:restrictions:country:allowed" content="LT"/><meta property="og:restrictions:country:allowed" content="LU"/><meta property="og:restrictions:country:allowed" content="LV"/><meta property="og:restrictions:country:allowed" content="MA"/><meta property="og:restrictions:country:allowed" content="MC"/><meta property="og:restrictions:country:allowed" content="ME"/><meta property="og:restrictions:country:allowed" content="MG"/><meta property="og:restrictions:country:allowed" content="MH"/><meta property="og:restrictions:country:allowed" content="MK"/><meta property="og:restrictions:country:allowed" content="ML"/><meta property="og:restrictions:country:allowed" content="MN"/><meta property="og:restrictions:country:allowed" content="MO"/><meta property="og:restrictions:country:allowed" content="MR"/><meta property="og:restrictions:country:allowed" content="MT"/><meta property="og:restrictions:country:allowed" content="MU"/><meta property="og:restrictions:country:allowed" content="MV"/><meta property="og:restrictions:country:allowed" content="MW"/><meta property="og:restrictions:country:allowed" content="MX"/><meta property="og:restrictions:country:allowed" content="MY"/><meta property="og:restrictions:country:allowed" content="MZ"/><meta property="og:restrictions:country:allowed" content="NA"/><meta property="og:restrictions:country:allowed" content="NE"/><meta property="og:restrictions:country:allowed" content="NG"/><meta property="og:restrictions:country:allowed" content="NI"/><meta property="og:restrictions:country:allowed" content="NL"/><meta property="og:restrictions:country:allowed" content="NO"/><meta property="og:restrictions:country:allowed" content="NP"/><meta property="og:restrictions:country:allowed" content="NR"/><meta property="og:restrictions:country:allowed" content="NZ"/><meta property="og:restrictions:country:allowed" content="OM"/><meta property="og:restrictions:country:allowed" content="PA"/><meta property="og:restrictions:country:allowed" content="PE"/><meta property="og:restrictions:country:allowed" content="PG"/><meta property="og:restrictions:country:allowed" content="PH"/><meta property="og:restrictions:country:allowed" content="PL"/><meta property="og:restrictions:country:allowed" content="PS"/><meta property="og:restrictions:country:allowed" content="PT"/><meta property="og:restrictions:country:allowed" content="PW"/><meta property="og:restrictions:country:allowed" content="PY"/><meta property="og:restrictions:country:allowed" content="QA"/><meta property="og:restrictions:country:allowed" content="RO"/><meta property="og:restrictions:country:allowed" content="RS"/><meta property="og:restrictions:country:allowed" content="RW"/><meta property="og:restrictions:country:allowed" content="SA"/><meta property="og:restrictions:country:allowed" content="SB"/><meta property="og:restrictions:country:allowed" content="SC"/><meta property="og:restrictions:country:allowed" content="SE"/><meta property="og:restrictions:country:allowed" content="SG"/><meta property="og:restrictions:country:allowed" content="SI"/><meta property="og:restrictions:country:allowed" content="SK"/><meta property="og:restrictions:country:allowed" content="SL"/><meta property="og:restrictions:country:allowed" content="SM"/><meta property="og:restrictions:country:allowed" content="SN"/><meta property="og:restrictions:country:allowed" content="SR"/><meta property="og:restrictions:country:allowed" content="ST"/><meta property="og:restrictions:country:allowed" content="SV"/><meta property="og:restrictions:country:allowed" content="SZ"/><meta property="og:restrictions:country:allowed" content="TD"/><meta property="og:restrictions:country:allowed" content="TG"/><meta property="og:restrictions:country:allowed" content="TH"/><meta property="og:restrictions:country:allowed" content="TL"/><meta property="og:restrictions:country:allowed" content="TN"/><meta property="og:restrictions:country:allowed" content="TO"/><meta property="og:restrictions:country:allowed" content="TR"/><meta property="og:restrictions:country:allowed" content="TT"/><meta property="og:restrictions:country:allowed" content="TV"/><meta property="og:restrictions:country:allowed" content="TW"/><meta property="og:restrictions:country:allowed" content="TZ"/><meta property="og:restrictions:country:allowed" content="UA"/><meta property="og:restrictions:country:allowed" content="US"/><meta property="og:restrictions:country:allowed" content="UY"/><meta property="og:restrictions:country:allowed" content="UZ"/><meta property="og:restrictions:country:allowed" content="VC"/><meta property="og:restrictions:country:allowed" content="VN"/><meta property="og:restrictions:country:allowed" content="VU"/><meta property="og:restrictions:country:allowed" content="WS"/><meta property="og:restrictions:country:allowed" content="XK"/><meta property="og:restrictions:country:allowed" content="ZA"/><meta property="og:restrictions:country:allowed" content="ZM"/><meta property="og:restrictions:country:allowed" content="ZW"/><meta name="music:song" content="https://open.spotify.com/episode/29iLg98zT2ysKTU6HqmK1r"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="1"/><meta name="music:song" content="https://open.spotify.com/episode/64mxcLZblfnkdb8uFRUPBq"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="2"/><meta name="music:song" content="https://open.spotify.com/episode/4hfegsO5ppgNhifrS2UO6D"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="3"/><meta name="music:song" content="https://open.spotify.com/episode/64q0oRGBJILRgWDEjIFjtD"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="4"/><meta name="music:song" content="https://open.spotify.com/episode/5lGE3iknhxc4xGI79bVcCe"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="5"/><meta name="music:song" content="https://open.spotify.com/episode/2u3ILMpA5jR5UXsYn01ZKp"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="6"/><meta name="music:song" content="https://open.spotify.com/episode/4mvmSvVtRdR10nJndCeywe"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="7"/><meta name="music:song" content="https://open.spotify.com/episode/75anOBJoLTr5E3d0kZjbWS"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="8"/><meta name="music:song" content="https://open.spotify.com/episode/6whdJI2FwFda1VXc0W7keI"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="9"/><meta name="music:song" content="https://open.spotify.com/episode/3FBvOQO1uCXHWkipk6Yjlg"/><meta name="music:song:disc" content="1"/><meta name="music:song:track" content="10"/><meta name="music:song_count" content="2137"/><meta name="al:android:app_name" content="Spotify"/><meta name="al:android:package" content="com.spotify.music"/><meta name="al:android:url" content="spotify://show/4rOoJ6Egrf8K2IrywzwOMk"/><meta name="al:ios:app_name" content="Spotify"/><meta name="al:ios:app_store_id" content="324684580"/><meta name="al:ios:url" content="spotify://show/4rOoJ6Egrf8K2IrywzwOMk"/><meta name="twitter:site" content="@spotify"/><meta name="twitter:title" content="The Joe Rogan Experience"/><meta name="twitter:description" content="Listen to The Joe Rogan Experience on Spotify. The official podcast of comedian Joe Rogan. Follow The Joe Rogan Clips show page for some of the best moments from the episodes."/><meta name="twitter:image" content="https://i.scdn.co/image/9af79fd06e34dea3cd27c4e1cd6ec7343ce20af4"/><meta name="twitter:card" content="summary"/><link rel="canonical" href="https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk"/><link rel="alternate" type="application/json+oembed" href="https://open.spotify.com/oembed?url=https%3A%2F%2Fopen.spotify.com%2Fshow%2F4rOoJ6Egrf8K2IrywzwOMk"/><link rel="alternate" href="https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk" hrefLang="x-default"/><link rel="alternate" href="https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk" hrefLang="en"/><link rel="alternate" href="android-app://com.spotify.music/spotify/show/4rOoJ6Egrf8K2IrywzwOMk"/><script type="application/ld+json">{"@context":"http://schema.org/","@type":"PodcastSeries","url":"https://open.spotify.com/show/4rOoJ6Egrf8K2IrywzwOMk","name":"The Joe Rogan Experience","description":"Listen to The Joe Rogan Experience on Spotify. The official podcast of comedian Joe Rogan. Follow The Joe Rogan Clips show page for some of the best moments from the episodes.","publisher":"Joe Rogan","author":{"@type":"Person","name":"Joe Rogan"},"image":"https://i.scdn.co/image/9af79fd06e34dea3cd27c4e1cd6ec7343ce20af4","accessMode":"auditory","inLanguage":"en-US"}</script><link rel="manifest" href="https://open.spotifycdn.com/cdn/generated/manifest-web-player.3a6f5207.json"/><link rel="stylesheet" href="https://open.spotifycdn.com/cdn/build/web-player/web-player.86894802.css"/><link rel="stylesheet" href="https://open.spotifycdn.com/cdn/build/web-player/vendor~web-player.dc79e26c.css"/><link rel="preconnect" href="https://api.spotify.com" crossorigin="anonymous"/><link rel="preconnect" href="https://apresolve.spotify.com" crossorigin="anonymous"/><link rel="preconnect" href="https://daily-mix.scdn.co" crossorigin="anonymous"/><link rel="preconnect" href="https://exp.wg.spotify.com" crossorigin="anonymous"/><link rel="preconnect" href="https://i.scdn.co" crossorigin="anonymous"/><link rel="preconnect" href="https://lineup-images.scdn.co" crossorigin="anonymous"/><link rel="preconnect" href="https://mosaic.scdn.co" crossorigin="anonymous"/><link rel="preconnect" href="https://open.spotifycdn.com" crossorigin="anonymous"/><link rel="preconnect" href="https://pixel-static.spotify.com" crossorigin="anonymous"/><link rel="preconnect" href="https://pixel.spotify.com" crossorigin="anonymous"/><link rel="preconnect" href="https://pl.scdn.co" crossorigin="anonymous"/><link rel="preconnect" href="https://spclient.wg.spotify.com" crossorigin="anonymous"/><link rel="preconnect" href="https://gew4-dealer.spotify.com" crossorigin="anonymous"/><link rel="preconnect" href="https://gew4-spclient.spotify.com" crossorigin="anonymous"/><link rel="preload" href="https://open.spotifycdn.com/cdn/generated-locales/web-player/en.2cb0106f.json" data-translations-url-for-locale="en" as="fetch" crossorigin="anonymous" type="application/json"/><style>.grecaptcha-badge { display: none !important;}</style><script src="https://www.google.com/recaptcha/enterprise.js?render=6LfCVLAUAAAAALFwwRnnCJ12DalriUGbj8FW_J39" async="" defer=""></script><link rel="search" type="application/opensearchdescription+xml" title="Spotify" href="https://open.spotifycdn.com/cdn/generated/opensearch.4cd8879e.xml"/><script defer="" src="https://www.googleoptimize.com/optimize.js?id=GTM-W53X654"></script><script defer="" src="https://open.spotifycdn.com/cdn/js/gtm.b8054d69.js"></script><script defer="" src="https://open.spotifycdn.com/cdn/js/retargeting-pixels.c038ca53.js"></script></head><body><div class="body-drag-top"></div><script id="config" data-testid="config" type="application/json">{"appName":"web_player_prototype","market":"PL","locale":{"locale":"en","rtl":false,"textDirection":"ltr"},"isPremium":false,"correlationId":"9979d88f56b8618b4ebd82e8bd5ced86","isAnonymous":true,"gtmId":"GTM-PZHN3VD","optimizeId":"GTM-W53X654","retargetingPixels":null,"recaptchaWebPlayerFraudSiteKey":"6LfCVLAUAAAAALFwwRnnCJ12DalriUGbj8FW_J39"}</script><script id="session" data-testid="session" type="application/json">{"accessToken":"BQDGy3VmnIZHVaZDUWPbOFdrCV_lpXt71v6YyC0zNY3RLkyTulruOmtzAQxffaWjCpuS_Rew7Srt5knh9XtLIhhU-4hZsqYTKF2MWBZvJBI-5VoEoNo","accessTokenExpirationTimestampMs":1685970062570,"isAnonymous":true,"clientId":"d8a5ed958d274c2e8ee717e6a4b0971d"}</script><script id="features" type="application/json">{"enableShows":true,"isTracingEnabled":false,"upgradeButton":"control","mwp":false,"isMWPErrorCodeEnabled":false,"isMwpRadioEntity":true,"isMWPAndPlaybackCapable":false,"preauthRecaptcha":false,"isEqualizerABEnabled":false,"isPodcastEnabled":true,"isPodcastSeoEnabled":true,"enableI18nLocales":true,"isI18nAdditionalPagesEnabled":false,"isAudiobooksOnMWPEnabled":false,"isPathfinderBrowseCardsEnabled":false,"isReinventFreeEnabled":false,"isRTPTrackCreditsEnabled":false,"isBlendPartyEnabled":false,"isBlendPartyV2Enabled":false,"isEntityReportEnabled":true,"isAlbumReportEnabled":false,"isTrackReportEnabled":false,"isPodcastShowReportEnabled":false,"isPodcastEpisodeReportEnabled":false}</script><script id="seo" type="application/json">{"show":{"4rOoJ6Egrf8K2IrywzwOMk":{"experimentId":"podcast-video-title-tag","treatment":"1"}}}</script><script id="remote-configuration" type="text/plain">eyIjdiI6IjEiLCJlbmFibGVDb3ZpZEh1YkJhbm5lciI6dHJ1ZSwiZW5hYmxlQ29udGVudEluZm9ybWF0aW9uTWVzc2FnZSI6dHJ1ZSwiZW5hYmxlTmV3UG9kY2FzdFRyYW5zY3JpcHRzIjp0cnVlLCJlbmFibGVBdWRpb2Jvb2tzIjp0cnVlLCJlbmFibGVJMThuUm91dGVzIjoidmFyaWFudCIsImVuYWJsZVVzZXJGcmF1ZFZlcmlmaWNhdGlvbiI6dHJ1ZSwiZW5hYmxlVXNlckZyYXVkU2lnbmFscyI6dHJ1ZSwiI2NvbmZpZ3VyYXRpb25Bc3NpZ25tZW50SWQiOiJiMmQ1NDAxZC1hOGNiLTViNzctMjExYi00NzBkNDMxNzNkNTMiLCIjZ3JvdXBJZHMiOnsiZW5hYmxlQ292aWRIdWJCYW5uZXIiOjEwMzUwNjMsImVuYWJsZUNvbnRlbnRJbmZvcm1hdGlvbk1lc3NhZ2UiOjEwMzUxNzQsImVuYWJsZU5ld1BvZGNhc3RUcmFuc2NyaXB0cyI6MTA0MjA3NiwiZW5hYmxlQXVkaW9ib29rcyI6MTA2ODczMiwiZW5hYmxlSTE4blJvdXRlcyI6MTEwMjY2MSwiZW5hYmxlVXNlckZyYXVkVmVyaWZpY2F0aW9uIjoxMDk2NjQxLCJlbmFibGVVc2VyRnJhdWRTaWduYWxzIjoxMTA5MjQzfSwiI2ZldGNoVGltZU1pbGxpcyI6MTY4NTk2NjkwMTkzMiwiI2NvbnRleHRIYXNoIjoiZjg5NDliNGMwODg0ZDAzNSJ9</script><script src="https://open.spotifycdn.com/cdn/build/web-player/web-player.de121931.js"></script><script src="https://open.spotifycdn.com/cdn/build/web-player/vendor~web-player.84d40124.js"></script></body></html>
    """

    from ..sources.rsssourceprocessor import RssSourceProcessor

    source = SourceDataModel.objects.get(id = pk)

    proc = RssSourceProcessor()
    proc.process_parser_source(source, text)

    context["summary_text"] = "Added to waybacksave"

    return render(request, get_app() / 'summary_present.html', context)


def import_youtube_links_for_source(request, pk):
    from ..programwrappers.ytdlp import YTDLP

    summary_text = ""
    context = get_context(request)
    context['page_title'] += " - import sources"

    if not request.user.is_staff:
        return render(request, get_app() / 'missing_rights.html', context)

    source_obj = SourceDataModel.objects.get(id = pk)
    url = str(source_obj.url)
    wh = url.find("=")

    if wh == -1:
        context['summary_text'] = "Could not obtain code from a video"
        return render(request, get_app() / 'summary_present.html', context)

    code = url[wh + 1 :]
    channel = 'https://www.youtube.com/channel/{}'.format(code)
    ytdlp = YTDLP(channel)
    links = ytdlp.get_channel_video_list()

    data = {"user" : None, "language" : source_obj.language, "persistent" : False}

    for link in links:
       print("Adding {}".format(link))
       try:
           LinkDataModel.create_from_youtube(link, data)
       except Exception as E:
           try:
               LinkDataModel.create_from_youtube(link, data)
           except Exception as E:
               pass

       summary_text += "\n{}".format(link)

    context['summary_text'] = summary_text
    return render(request, get_app() / 'summary_present.html', context)
