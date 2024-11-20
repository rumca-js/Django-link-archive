from django.db import models


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
    TYPE_DIGITAL_LIBRARY = "digital-library"
    TYPE_MARKETPLACE = "marketplace"

    GATEWAYS_TYPES = [
        TYPE_GATEWAY,
        TYPE_SEARCH_ENGINE,
        TYPE_AI_BOT,
        TYPE_POPULAR,
        TYPE_FAVOURITE,
        TYPE_SOCIAL_MEDIA,
        TYPE_AUDIO_STREAMING,
        TYPE_VIDEO_STREAMING,
        TYPE_DIGITAL_LIBRARY,
        TYPE_MARKETPLACE,
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
        [TYPE_DIGITAL_LIBRARY, TYPE_DIGITAL_LIBRARY],
        [TYPE_MARKETPLACE, TYPE_MARKETPLACE],
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

    def populate_search_engines():
        thetype = Gateway.TYPE_SEARCH_ENGINE

        Gateway.objects.create(link = "https://duckduckgo.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://startpage.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://google.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://bing.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://kagi.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://perplexity.ai", gateway_type=thetype)
        Gateway.objects.create(link = "https://wolframalpha.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://mwmbl.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://whoogle.io", gateway_type=thetype)
        Gateway.objects.create(link = "https://search.marginalia.nu", gateway_type=thetype)
        Gateway.objects.create(link = "https://yahoo.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://baidu.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://search.brave.com", gateway_type=thetype)
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

    def populate_digital_libraries():
        thetype = Gateway.TYPE_DIGITAL_LIBRARY

        Gateway.objects.create(link = "https://wikipedia.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://web.archive.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://archive.ph", gateway_type=thetype)
        Gateway.objects.create(link = "https://annas-archive.org", gateway_type=thetype)
        Gateway.objects.create(link = "https://github.com", gateway_type=thetype)

    def populate_video_streaming():
        thetype = Gateway.TYPE_VIDEO_STREAMING

        Gateway.objects.create(link = "https://yewtu.be", gateway_type=thetype)
        Gateway.objects.create(link = "https://youtube.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://odysee.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://tiktok.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://rumble.com", gateway_type=thetype)

    def populate_audio_streaming():
        thetype = Gateway.TYPE_AUDIO_STREAMING

        Gateway.objects.create(link = "https://open.spotify.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://music.youtube.com/", gateway_type=thetype)

    def populate_favourites():
        thetype = Gateway.TYPE_FAVOURITE

        Gateway.objects.create(link = "https://hn.algolia.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://news.ycombinator.com/", gateway_type=thetype)

    def populate_social_media():
        thetype = Gateway.TYPE_SOCIAL_MEDIA

        Gateway.objects.create(link = "https://reddit.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://quora.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://facebook.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://stackoverflow.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://linkedin.com", gateway_type=thetype)

    def populate_ai_bot():
        thetype = Gateway.TYPE_AI_BOT

        Gateway.objects.create(link = "https://chatgpt.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://bard.google.com", gateway_type=thetype)

    def populate_marketplaces():
        thetype = Gateway.TYPE_MARKETPLACE

        Gateway.objects.create(link = "https://amazon.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://aliexpress.com", gateway_type=thetype)
        Gateway.objects.create(link = "https://ebay.com", gateway_type=thetype)
