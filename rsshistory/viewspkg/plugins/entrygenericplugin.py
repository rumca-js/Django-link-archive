import urllib.parse

from django.urls import reverse
from django.templatetags.static import static

from ...apps import LinkDatabase
from ...models import ConfigurationEntry, UserConfig
from ...controllers import LinkDataController, SearchEngineGoogleCache
from ...webtools import DomainAwarePage, InputContent
from ...configuration import Configuration
from ...dateutils import DateUtils
from ...services import TranslateBuilder, InternetArchiveBuilder, SchemaOrg, WhoIs, W3CValidator



class EntryButton(object):
    def __init__(
        self,
        user,
        name,
        action,
        access=ConfigurationEntry.ACCESS_TYPE_LOGGED,
        title=None,
        image=None,
    ):
        self.user = user
        self.name = name
        self.action = action
        self.image = image
        self.access = access
        self.title = title

    def is_shown(self):
        if self.access == ConfigurationEntry.ACCESS_TYPE_ALL:
            return True

        if self.access == ConfigurationEntry.ACCESS_TYPE_LOGGED and (
            self.user.is_staff or self.user.is_authenticated
        ):
            return True

        if self.access == ConfigurationEntry.ACCESS_TYPE_OWNER and (self.user.is_staff):
            return True

        return False


class EntryParameter(object):
    def __init__(self, name, description, title=None):
        self.name = name
        self.description = description
        self.title = title


class EntryGenericPlugin(object):
    def __init__(self, entry, user=None):
        self.entry = entry
        self.user = user

    def encode_url(self, url):
        return urllib.parse.quote(url)

    def set_user(self, user):
        self.user = user

    def get_menu_buttons(self):
        return []

    def get_edit_menu_buttons(self):
        buttons = []
        config = Configuration.get_object().config_entry

        if self.user.is_authenticated:
            buttons.append(
                EntryButton(
                    self.user,
                    "Edit",
                    self.entry.get_edit_url(),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Edit entry",
                    static("{}/icons/icons8-edit-100.png".format(LinkDatabase.name)),
                ),
            )

        if self.user.is_authenticated:
            if self.entry.bookmarked:
                buttons.append(
                    EntryButton(
                        self.user,
                        "Unbookmark",
                        self.entry.get_bookmark_unset_url(),
                        ConfigurationEntry.ACCESS_TYPE_OWNER,
                        "Unbookmark entry",
                        static(
                            "{}/icons/icons8-not-bookmark-100.png".format(
                                LinkDatabase.name
                            )
                        ),
                    )
                )
            else:
                buttons.append(
                    EntryButton(
                        self.user,
                        "Bookmark",
                        self.entry.get_bookmark_set_url(),
                        ConfigurationEntry.ACCESS_TYPE_OWNER,
                        "Bookmark entry",
                        static(
                            "{}/icons/icons8-bookmark-100.png".format(LinkDatabase.name)
                        ),
                    )
                )

        if self.user.is_authenticated:
            if self.entry.is_taggable():
                buttons.append(
                    EntryButton(
                        self.user,
                        "Vote",
                        reverse(
                            "{}:entry-vote".format(LinkDatabase.name),
                            args=[self.entry.id],
                        ),
                        ConfigurationEntry.ACCESS_TYPE_OWNER,
                        "Vote on entry",
                        static(
                            "{}/icons/icons8-rate-100.png".format(LinkDatabase.name)
                        ),
                    ),
                )

        if self.entry.is_taggable():
            if self.user.is_authenticated:
                buttons.append(
                    EntryButton(
                        self.user,
                        "Tag",
                        reverse(
                            "{}:entry-tag".format(LinkDatabase.name),
                            args=[self.entry.id],
                        ),
                        ConfigurationEntry.ACCESS_TYPE_OWNER,
                        "Tags entry: {}".format(self.entry.title),
                        static(
                            "{}/icons/icons8-edit-100.png".format(LinkDatabase.name)
                        ),
                    ),
                )

        if self.user.is_authenticated:
            buttons.append(
                EntryButton(
                    self.user,
                    "Update data",
                    reverse(
                        "{}:entry-update-data".format(LinkDatabase.name),
                        args=[self.entry.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Updates entry data",
                    static("{}/icons/icons8-update-100.png".format(LinkDatabase.name)),
                ),
            )

        if self.user.is_authenticated:
            buttons.append(
                EntryButton(
                    self.user,
                    "Reset data",
                    reverse(
                        "{}:entry-reset-data".format(LinkDatabase.name),
                        args=[self.entry.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Resets entry data",
                    static(
                        "{}/icons/icons8-update-skull-100.png".format(LinkDatabase.name)
                    ),
                ),
            )

        if self.user.is_authenticated:
            buttons.append(
                EntryButton(
                    self.user,
                    "Reset local data",
                    reverse(
                        "{}:entry-reset-local-data".format(LinkDatabase.name),
                        args=[self.entry.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Resets entry local data",
                    static("{}/icons/icons8-update-100.png".format(LinkDatabase.name)),
                ),
            )

        if self.user.is_authenticated:
            buttons.append(
                EntryButton(
                    self.user,
                    "Scan link",
                    reverse(
                        "{}:page-scan-link".format(LinkDatabase.name),
                    )
                    + "?link={}".format(self.entry.link),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Scans entry for new links",
                    static("{}/icons/icons8-radar-64.png".format(LinkDatabase.name)),
                ),
            )

        if self.user.is_authenticated:
            if not self.entry.source_obj or not self.is_entry_share_source_domain():
                buttons.append(
                    EntryButton(
                        self.user,
                        "Add source",
                        reverse(
                            "{}:source-add-simple".format(LinkDatabase.name),
                        )
                        + "?link={}".format(self.entry.link),
                        ConfigurationEntry.ACCESS_TYPE_OWNER,
                        "Add new source",
                        static(
                            "{}/icons/icons8-broadcast-add-100.png".format(
                                LinkDatabase.name
                            )
                        ),
                    ),
                )

        if self.user.is_authenticated:
            buttons.append(
                EntryButton(
                    self.user,
                    "Save",
                    reverse(
                        "{}:entry-save".format(LinkDatabase.name),
                        args=[self.entry.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Saves link in archive.org: {}".format(self.entry.link),
                    static("{}/icons/archive.org.save.ico".format(LinkDatabase.name)),
                ),
            )

        if self.user.is_authenticated:
            if not self.entry.is_dead():
                buttons.append(
                    EntryButton(
                        self.user,
                        "Mark Dead",
                        reverse(
                            "{}:entry-dead".format(LinkDatabase.name),
                            args=[self.entry.id],
                        ),
                        ConfigurationEntry.ACCESS_TYPE_OWNER,
                        "Marks entry as dead:{}".format(self.entry.title),
                        static(
                            "{}/icons/icons8-skull-100.png".format(LinkDatabase.name)
                        ),
                    ),
                )
            else:
                buttons.append(
                    EntryButton(
                        self.user,
                        "Mark not dead",
                        reverse(
                            "{}:entry-not-dead".format(LinkDatabase.name),
                            args=[self.entry.id],
                        ),
                        ConfigurationEntry.ACCESS_TYPE_OWNER,
                        "Marks entry as not dead:{}".format(self.entry.title),
                        static(
                            "{}/icons/icons8-show-100.png".format(LinkDatabase.name)
                        ),
                    ),
                )

        if self.user.is_authenticated:
            buttons.append(
                EntryButton(
                    self.user,
                    "Remove",
                    reverse(
                        "{}:entry-remove".format(LinkDatabase.name),
                        args=[self.entry.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Removes entry: {}".format(self.entry.title),
                    static("{}/icons/icons8-trash-100.png".format(LinkDatabase.name)),
                ),
            )

        return buttons

    def is_entry_share_source_domain(self):
        if not self.entry.source_obj:
            return False

        entry_domain = DomainAwarePage(self.entry.link).get_domain()
        source_domain = DomainAwarePage(self.entry.source_obj.url).get_domain()

        return entry_domain == source_domain

    def get_view_menu_buttons(self):
        config = Configuration.get_object().config_entry
        buttons = []

        translate_url = TranslateBuilder.get(self.entry.link).get_translate_url()

        p = DomainAwarePage(self.entry.link)
        p_up = p.up(skip_internal=True)

        if p_up:
            search_url = p_up.url
            buttons.append(
                EntryButton(
                    self.user,
                    "[S] Parent entry",
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=link+%3D+{}".format(search_url),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Parent Entry: {}".format(search_url),
                ),
            )

        if self.entry.link.startswith("http://"):
            search_url = self.entry.link.replace("http://", "https://")

            buttons.append(
                EntryButton(
                    self.user,
                    "[S] https entry",
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=link+%3D+{}".format(search_url),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Https Entry: {}".format(search_url),
                ),
            )

        if self.entry.source_obj:
            search_url = self.entry.source_obj.url

            buttons.append(
                EntryButton(
                    self.user,
                    "[S] Source Entry",
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=link+%3D+{}".format(search_url),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Source Entry: {}".format(self.entry.source_obj.title),
                    static("{}/icons/icons8-link-90.png".format(LinkDatabase.name)),
                ),
            )

        if self.entry.artist and self.entry.artist != "":
            buttons.append(
                EntryButton(
                    self.user,
                    "[S] Artist: " + self.entry.artist[:20],
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=artist+%3D+{}".format(self.entry.artist),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Search for entries made by {} artist".format(self.entry.artist),
                ),
            )

        if self.entry.album and self.entry.album != "":
            buttons.append(
                EntryButton(
                    self.user,
                    "[S] Album: " + self.entry.album[:20],
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=album+%3D+{}".format(self.entry.album),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Search for entries in {} album".format(self.entry.album),
                ),
            )

        if config.accept_domains and self.entry.domain_obj:
            buttons.append(
                EntryButton(
                    self.user,
                    "Domain",
                    reverse(
                        "{}:domain-detail".format(LinkDatabase.name),
                        args=[self.entry.domain_obj.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Domain: {}".format(self.entry.domain_obj.domain),
                    static("{}/icons/icons8-www-64.png".format(LinkDatabase.name)),
                ),
            )
        else:
            domain_url = DomainAwarePage(self.entry.link).get_domain()

            buttons.append(
                EntryButton(
                    self.user,
                    "[S] Domain",
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=link+%3D%3D+{}".format(domain_url),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Domain: {}".format(domain_url),
                    static("{}/icons/icons8-www-64.png".format(LinkDatabase.name)),
                ),
            )

        buttons.append(
            EntryButton(
                self.user,
                "Translate Page",
                translate_url,
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Translate Page",
            ),
        )

        date = self.entry.date_published
        builder = InternetArchiveBuilder.get(self.entry.link)
        archive_link = builder.get_archive_url(date)

        buttons.append(
            EntryButton(
                self.user,
                "Archived page",
                archive_link,
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Archive link: {}".format(archive_link),
                "https://archive.org/offshoot_assets/favicon.ico",
            ),
        )

        e = SearchEngineGoogleCache(self.entry.link)
        cache_link = e.get_search_string()

        buttons.append(
            EntryButton(
                self.user,
                "Cached page",
                cache_link,
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Cache link: {}".format(cache_link),
                "https://archive.org/offshoot_assets/favicon.ico",
            ),
        )

        return buttons

    def get_advanced_menu_buttons(self):
        buttons = []

        buttons.append(
            EntryButton(
                self.user,
                "Download page",
                reverse(
                    "{}:entry-download".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Downloads the page to configured location",
                static(
                    "{}/icons/icons8-download-page-96.png".format(LinkDatabase.name)
                ),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "Page properties",
                reverse(
                    "{}:page-show-props".format(LinkDatabase.name),
                )
                + "?page={}".format(self.entry.link),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Shows page properties",
                static(
                    "{}/icons/icons8-view-details-100.png".format(LinkDatabase.name)
                ),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "Show JSON",
                reverse(
                    "{}:entry-json".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Shows JSON data",
            ),
        )

        link = self.entry.link

        buttons.append(
            EntryButton(
                self.user,
                "Who Is",
                WhoIs(link).get_validate_url(),
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Shows Who is information",
                static(
                    "{}/icons/icons8-download-page-96.png".format(LinkDatabase.name)
                ),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "W3C validator",
                W3CValidator(link).get_validate_url(),
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Shows Who is information",
                static(
                    "{}/icons/icons8-download-page-96.png".format(LinkDatabase.name)
                ),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "Schema.org validator",
                SchemaOrg(link).get_validate_url(),
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Shows Who is information",
                static(
                    "{}/icons/icons8-download-page-96.png".format(LinkDatabase.name)
                ),
            ),
        )

        return buttons

    def get_parameters(self):
        parameters = []

        c = Configuration.get_object()
        date_published = c.get_local_time(self.entry.date_published)
        parameters.append(EntryParameter("Publish date", date_published))

        return parameters

    def get_parameters_operation(self):
        c = Configuration.get_object()

        parameters = []

        points_text = "P:{}|C:{}|V:{}".format(
            self.entry.page_rating,
            self.entry.page_rating_contents,
            self.entry.page_rating_votes,
        )
        points_title = "Page rating:{} Content rating:{} User rating:{}".format(
            self.entry.page_rating,
            self.entry.page_rating_contents,
            self.entry.page_rating_votes,
        )
        parameters.append(EntryParameter("Points", points_text, points_title))

        update_date = c.get_local_time(self.entry.date_update_last)
        parameters.append(EntryParameter("Update date", update_date))

        modified_date = c.get_local_time(self.entry.date_last_modified)
        parameters.append(EntryParameter("Modified date", modified_date))

        parameters.append(EntryParameter("Status code", self.entry.status_code))

        parameters.append(EntryParameter("Language", self.entry.language))
        if self.entry.is_dead():
            parameters.append(
                EntryParameter("Manual status", self.entry.manual_status_code)
            )
            date_dead_since = c.get_local_time(self.entry.date_dead_since)
            parameters.append(EntryParameter("Dead since", date_dead_since))

        # Artist & album are displayed in buttons
        # Page rating is displayed in title

        parameters.append(EntryParameter("Visists", self.entry.page_rating_visits))

        if self.entry.user != "":
            parameters.append(EntryParameter("User", self.entry.user))

        return parameters

    def get_frame_html(self):
        u = UserConfig.get(self.user)

        if not u.show_icons:
            return ""

        thumbnail = self.entry.get_thumbnail()
        if not thumbnail:
            return ""

        if not self.entry.is_user_appropriate(self.user):
            frame_text = """
            <a href="{}">
            <div style="color:red">This material is restricted for age {}</div>
            </a>
            """

            frame_text = frame_text.format(self.entry.link, self.entry.age)

            return frame_text
        else:
            frame_text = """
            <a href="{}">
            <div>
                <img src="{}" class="link-detail-thumbnail"/>
            </div>
            </a>
            """

            frame_text = frame_text.format(self.entry.link, self.entry.get_thumbnail())
            return frame_text

    def get_title_html(self):
        if not self.entry.is_user_appropriate(self.user):
            return "Adult content"

        return self.entry.title

    def get_description_html(self):
        if not self.entry.is_user_appropriate(self.user):
            return "Adult content"

        description = self.entry.description
        if not description or description == "":
            return ""

        return """{}""".format(InputContent(description).htmlify())
