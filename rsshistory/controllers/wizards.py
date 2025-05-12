from django.conf import settings
from ..configuration import Configuration

from ..models import (
    ConfigurationEntry,
    UserConfig,
    EntryRules,
    SearchView,
)
from .backgroundjob import BackgroundJobController


def common_initialization():
    EntryRules.initialize_common_rules()

    SearchView.objects.create(
        name="Search by votes",
        order_by="-page_rating_votes, -page_rating, link",
        entry_limit=1000,
        hover_text="Search by votes",
    )
    SearchView.objects.create(
        name="What's created",
        order_by="-date_created, link",
        date_published_day_limit=7,
        hover_text="Search by date created",
    )
    SearchView.objects.create(
        name="What's published",
        order_by="-date_published, link",
        date_published_day_limit=7,
        hover_text="Search by date published",
    )


def system_setup_for_news(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    UserConfig.get_or_create(request.user)

    c = ConfigurationEntry.get()
    c.enable_link_archiving = True
    c.enable_source_archiving = False
    c.accept_dead_links = False
    c.accpte_ip_addresses = False
    c.auto_scan_new_entries = False
    c.accept_non_domain_links = True
    c.auto_store_sources = False
    c.accept_domain_links = False
    c.enable_keyword_support = True
    c.track_user_actions = True
    c.track_user_searches = True
    c.track_user_navigation = False
    c.days_to_move_to_archive = 100
    c.days_to_check_stale_entries = 10
    c.days_to_remove_links = 20
    c.days_to_remove_stale_entries = 0  # do not remove bookmarks?
    c.prefer_https_links = False
    c.display_type = ConfigurationEntry.DISPLAY_TYPE_STANDARD
    c.default_search_behavior = ConfigurationEntry.SEARCH_BUTTON_RECENT
    if settings.CRAWLER_BUDDY_URL:
        c.remote_webtools_server_location = "http://" + settings.CRAWLER_BUDDY_URL

    c.initialized = True

    c.save()

    Configuration.get_object().config_entry.refresh_from_db()

    SearchView.objects.create(
        name="Default",
        order_by="-date_created, link",
        default=True,
        hover_text="Search",
    )
    common_initialization()
    SearchView.objects.create(
        name="Bookmarked",
        filter_statement="bookmarked=True",
        order_by="-date_created, link",
        user=True,
        hover_text="Search bookmarks",
    )
    SearchView.objects.create(
        name="Searchs all entries", order_by="-date_created, link", hover_text="Search"
    )

    return True


def system_setup_for_gallery(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    UserConfig.get_or_create(request.user)

    c = ConfigurationEntry.get()
    c.enable_link_archiving = False
    c.enable_source_archiving = False
    c.accept_dead_links = False
    c.accpte_ip_addresses = False
    c.auto_scan_new_entries = False
    c.accept_non_domain_links = True
    c.auto_store_sources = False
    c.accept_domain_links = False
    c.enable_keyword_support = False
    c.track_user_actions = True
    c.track_user_searches = True
    c.track_user_navigation = True
    c.days_to_move_to_archive = 0
    c.days_to_check_stale_entries = 10
    c.days_to_remove_links = 30
    c.days_to_remove_stale_entries = 0  # do not remove bookmarks?
    c.prefer_https_links = False
    c.display_type = ConfigurationEntry.DISPLAY_TYPE_GALLERY
    c.default_search_behavior = ConfigurationEntry.SEARCH_BUTTON_ALL
    if settings.CRAWLER_BUDDY_URL:
        c.remote_webtools_server_location = "http://" + settings.CRAWLER_BUDDY_URL

    c.initialized = True

    c.save()

    Configuration.get_object().config_entry.refresh_from_db()

    SearchView.objects.create(
        name="Default", order_by="-date_created, link", default=True
    )
    common_initialization()
    SearchView.objects.create(
        name="Bookmarked",
        filter_statement="bookmarked=True",
        order_by="-date_published,-date_created, link",
        user=True,
        hover_text="Search bookmarks",
    )
    SearchView.objects.create(
        name="Searchs all entries", order_by="-date_created, link", hover_text="Search"
    )

    return True


def system_setup_for_search_engine(request):
    """
    Displays form, or textarea of available links.
    User can select which links will be added.
    """
    UserConfig.get_or_create(request.user)

    c = ConfigurationEntry.get()
    c.enable_link_archiving = False
    c.enable_source_archiving = False
    c.accept_dead_links = False
    c.accpte_ip_addresses = False
    c.auto_scan_new_entries = True
    c.accept_non_domain_links = True
    c.auto_store_sources = True
    c.accept_domain_links = True
    c.enable_keyword_support = False
    c.track_user_actions = True
    c.track_user_searches = True
    c.track_user_navigation = (
        False  # it would be interesting for the search engine though
    )
    c.days_to_move_to_archive = 0
    c.days_to_check_stale_entries = 10
    c.days_to_remove_links = 30
    c.days_to_remove_stale_entries = 30
    c.prefer_https_links = True
    c.display_type = ConfigurationEntry.DISPLAY_TYPE_SEARCH_ENGINE
    c.default_search_behavior = ConfigurationEntry.SEARCH_BUTTON_ALL
    c.remove_entry_vote_threshold = (
        1  # do not remove everything above, or equal to 1 vote
    )
    if settings.CRAWLER_BUDDY_URL:
        c.remote_webtools_server_location = "http://" + settings.CRAWLER_BUDDY_URL

    c.initialized = True

    c.save()

    Configuration.get_object().config_entry.refresh_from_db()

    SearchView.objects.create(
        name="Default", order_by="-page_rating_votes, -page_rating, link", default=True
    )
    common_initialization()
    SearchView.objects.create(
        name="Bookmarked",
        filter_statement="bookmarked=True",
        order_by="-page_rating_votes, -page_rating, link",
        user=True,
        hover_text="Search bookmarks",
    )
    SearchView.objects.create(
        name="Searchs all entries",
        order_by="-page_rating_votes, -page_rating, link",
        hover_text="Search",
    )

    # we want blocklist to be enabled for search engine
    BackgroundJobController.create_single_job(BackgroundJobController.JOB_INITIALIZE)

    return True
