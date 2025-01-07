from django.db import models

from collections import OrderedDict


class Gateway(models.Model):
    """
    Gateways were introduced when amazon, google, and others were checked by EU
    to see if they should be split.

    This table should be small, should contain limited amount of entries.

    I think many more pages, plarforms are gateways to the internet, and should be
    kept in check.
    """

    TYPE_GATEWAY = "gateway" # generally acknowledged as popular
    TYPE_SEARCH_ENGINE = "search-engine"
    TYPE_AI_BOT = "ai-bot"
    TYPE_POPULAR = "popular" # popular in this instance. 5 most popular entries, by a visit?
    TYPE_SOCIAL_MEDIA = "social-media"
    TYPE_FAVOURITE = "favourite"
    TYPE_AUDIO_STREAMING = "audio-streaming"
    TYPE_VIDEO_STREAMING = "video-streaming"
    TYPE_FILE_SHARING = "file-sharing"
    TYPE_BANKING = "banking"
    TYPE_DIGITAL_LIBRARY = "digital-library"
    TYPE_MARKETPLACE = "marketplace"
    TYPE_APP_STORE = "app-store"
    TYPE_OTHER = "other"

    GATEWAYS_TYPES = [
        TYPE_GATEWAY,
        TYPE_SEARCH_ENGINE,
        TYPE_AI_BOT,
        TYPE_POPULAR,
        TYPE_FAVOURITE,
        TYPE_SOCIAL_MEDIA,
        TYPE_AUDIO_STREAMING,
        TYPE_VIDEO_STREAMING,
        TYPE_FILE_SHARING,
        TYPE_BANKING,
        TYPE_DIGITAL_LIBRARY,
        TYPE_MARKETPLACE,
        TYPE_APP_STORE,
        TYPE_OTHER,
    ]

    GATEWAYS_CHOICES = [
        [TYPE_GATEWAY, TYPE_GATEWAY],
        [TYPE_SEARCH_ENGINE, TYPE_SEARCH_ENGINE],
        [TYPE_AI_BOT, TYPE_AI_BOT],
        [TYPE_POPULAR, TYPE_POPULAR],
        [TYPE_SOCIAL_MEDIA, TYPE_SOCIAL_MEDIA],
        [TYPE_FAVOURITE, TYPE_FAVOURITE],
        [TYPE_AUDIO_STREAMING, TYPE_AUDIO_STREAMING],
        [TYPE_VIDEO_STREAMING, TYPE_VIDEO_STREAMING],
        [TYPE_FILE_SHARING, TYPE_FILE_SHARING],
        [TYPE_BANKING, TYPE_BANKING],
        [TYPE_DIGITAL_LIBRARY, TYPE_DIGITAL_LIBRARY],
        [TYPE_MARKETPLACE, TYPE_MARKETPLACE],
        [TYPE_APP_STORE, TYPE_APP_STORE],
        [TYPE_OTHER, TYPE_OTHER],
    ]

    link = models.CharField(max_length=1000, unique=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    description = models.TextField(max_length=1000, null=True, blank=True)
    gateway_type = models.CharField(max_length=1000, choices=GATEWAYS_CHOICES, null=True, blank=True) # TYPE

    def cleanup(cfg = None):
        """
        Should:
         - remove all popular, fetch new 5 top visited links, add it to popular here
         - clears social-media entries, adds "social media" from tags
         - clears search-engine entries, adds "search engine" from tags
        """

        full_cleanup = False
        if cfg and "full" in cfg:
            full_cleanup = True

        if full_cleanup:
            Gateway.objects.all().delete()
            Gateway.populate()

    def check_init():
        if Gateway.objects.all().count() == 0:
            Gateway.populate()

    def populate():
        Gateway.populate_search_engines()
        Gateway.populate_digital_libraries()
        Gateway.populate_video_streaming()
        Gateway.populate_audio_streaming()
        Gateway.populate_favourites()
        Gateway.populate_social_media()
        Gateway.populate_ai_bot()
        Gateway.populate_marketplaces()
        Gateway.populate_file_sharing()
        Gateway.populate_banking()
        Gateway.populate_app_store()
        Gateway.populate_other()

    def populate_search_engines():
        thetype = Gateway.TYPE_SEARCH_ENGINE

        Gateway.objects.create(link = "https://google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://bing.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://searxng.site", gateway_type=thetype)
        Gateway.objects.create(link = "https://4get.ca", gateway_type=thetype)
        Gateway.objects.create(link = "https://duckduckgo.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://kagi.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://search.brave.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://yahoo.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://startpage.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://wolframalpha.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://mwmbl.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://whoogle.io", gateway_type=thetype)
        Gateway.objects.create(link = "https://search.marginalia.nu", gateway_type=thetype)
        Gateway.objects.create(link = "https://baidu.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://mojeek.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://morphic.sh", gateway_type=thetype)
        Gateway.objects.create(link = "https://shodan.io", gateway_type=thetype)
        Gateway.objects.create(link = "https://sogou.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://stract.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://wiby.me", gateway_type=thetype)
        Gateway.objects.create(link = "https://cse.google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://anoox.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://greppr.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://letsearch.ru", gateway_type=thetype)
        Gateway.objects.create(link = "https://presearch.io", gateway_type=thetype)
        Gateway.objects.create(link = "https://yandex.com", gateway_type=thetype)

    def populate_digital_libraries():
        thetype = Gateway.TYPE_DIGITAL_LIBRARY

        Gateway.objects.create(link = "https://wikipedia.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://github.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://archive.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://archive.ph", gateway_type=thetype)
        Gateway.objects.create(link = "https://annas-archive.org", gateway_type=thetype)

    def populate_video_streaming():
        thetype = Gateway.TYPE_VIDEO_STREAMING

        Gateway.objects.create(link = "https://youtube.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://tiktok.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://netflix.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://disneyplus.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://rumble.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://odysee.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://yewtu.be", gateway_type=thetype)
        Gateway.objects.create(link = "https://twitch.tv", gateway_type=thetype)
        Gateway.objects.create(link = "https://dailymotion.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://vimeo.com", gateway_type=thetype)

    def populate_file_sharing():
        thetype = Gateway.TYPE_FILE_SHARING

        Gateway.objects.create(link = "https://drive.google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://icloud.com", gateway_type=thetype)

    def populate_banking():
        thetype = Gateway.TYPE_BANKING

        Gateway.objects.create(link = "https://paypal.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://wallet.google", gateway_type=thetype)
        Gateway.objects.create(link = "https://apple.com/pl/apple-pay", gateway_type=thetype)

    def populate_audio_streaming():
        thetype = Gateway.TYPE_AUDIO_STREAMING

        Gateway.objects.create(link = "https://open.spotify.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://music.youtube.com", gateway_type=thetype)

    def populate_favourites():
        thetype = Gateway.TYPE_FAVOURITE

    def populate_social_media():
        thetype = Gateway.TYPE_SOCIAL_MEDIA

        Gateway.objects.create(link = "https://meta.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://reddit.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://facebook.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://stackoverflow.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://linkedin.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://discord.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://messanger.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://whatsapp.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://instagram.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://quora.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://wechat.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://hn.algolia.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://news.ycombinator.com", gateway_type=thetype)

    def populate_ai_bot():
        thetype = Gateway.TYPE_AI_BOT

        Gateway.objects.create(link = "https://chatgpt.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://copilot.microsoft.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://bard.google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://perplexity.ai", gateway_type=thetype)

    def populate_marketplaces():
        thetype = Gateway.TYPE_MARKETPLACE

        Gateway.objects.create(link = "https://amazon.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://aliexpress.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://ebay.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://facebook.com/marketplace", gateway_type=thetype)
        Gateway.objects.create(link = "https://vinted.com", gateway_type=thetype)

    def populate_app_store():
        thetype = Gateway.TYPE_APP_STORE

        Gateway.objects.create(link = "https://play.google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://store.steampowered.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://apps.apple.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://store.playstation.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://shop.battle.net", gateway_type=thetype)

    def populate_other():
        thetype = Gateway.TYPE_OTHER

        Gateway.objects.create(link = "https://gmail.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://maps.google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://chrome.google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://office.com/", gateway_type=thetype)
        Gateway.objects.create(link = "https://apple.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://microsoft.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://microsoft.com/microsoft-teams", gateway_type=thetype)

    def get_types_mapping(gateway_types):
        data = OrderedDict()
        if Gateway.TYPE_SEARCH_ENGINE in gateway_types:
            data["search_engines"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_SEARCH_ENGINE)
        if Gateway.TYPE_AI_BOT in gateway_types:
            data["ai_search_engines"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_AI_BOT)
        if Gateway.TYPE_DIGITAL_LIBRARY in gateway_types:
            data["digital_library"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_DIGITAL_LIBRARY)
        if Gateway.TYPE_GATEWAY in gateway_types:
            data["gateways"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_GATEWAY)
        if Gateway.TYPE_APP_STORE in gateway_types:
            data["app_store"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_APP_STORE)
        if Gateway.TYPE_POPULAR in gateway_types:
            data["popular"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_POPULAR)
        if Gateway.TYPE_FAVOURITE in gateway_types:
            data["favourite"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_FAVOURITE)
        if Gateway.TYPE_SOCIAL_MEDIA in gateway_types:
            data["social_media"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_SOCIAL_MEDIA)
        if Gateway.TYPE_AUDIO_STREAMING in gateway_types:
            data["audio_streaming"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_AUDIO_STREAMING)
        if Gateway.TYPE_VIDEO_STREAMING in gateway_types:
            data["video_streaming"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_VIDEO_STREAMING)
        if Gateway.TYPE_MARKETPLACE in gateway_types:
            data["marketplace"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_MARKETPLACE)
        if Gateway.TYPE_FILE_SHARING in gateway_types:
            data["file_sharing"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_FILE_SHARING)
        if Gateway.TYPE_BANKING in gateway_types:
            data["banking"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_BANKING)
        if Gateway.TYPE_OTHER in gateway_types:
            data["other"] = Gateway.objects.filter(gateway_type = Gateway.TYPE_OTHER)

        return data
