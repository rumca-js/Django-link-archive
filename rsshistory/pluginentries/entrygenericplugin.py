from django.urls import reverse
from django.templatetags.static import static

from ..apps import LinkDatabase
from ..models import ConfigurationEntry
from ..webtools import HtmlPage
from ..configuration import Configuration


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
    def __init__(self, name, description):
        self.name = name
        self.description = description


class EntryGenericPlugin(object):
    def __init__(self, entry, user=None):
        self.entry = entry
        self.user = user

    def set_user(self, user):
        self.user = user

    def get_menu_buttons(self):
        return []

    def get_edit_menu_buttons(self):
        buttons = []

        buttons.append(
            EntryButton(
                self.user,
                "",
                self.entry.get_edit_url(),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Edit entry",
                static("{}/icons/icons8-edit-100.png".format(LinkDatabase.name)),
            ),
        )

        if self.entry.bookmarked:
            buttons.append(
                EntryButton(
                    self.user,
                    "",
                    self.entry.get_bookmark_unset_url(),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Unbookmark entry",
                    static(
                        "{}/icons/icons8-not-bookmark-100.png".format(LinkDatabase.name)
                    ),
                )
            )
        else:
            buttons.append(
                EntryButton(
                    self.user,
                    "",
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
                    ),
                )

        buttons.append(
            EntryButton(
                self.user,
                "Page",
                reverse(
                    "{}:entry-download".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Downloads the page to configured location",
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "Page Props",
                reverse(
                    "{}:show-page-props".format(LinkDatabase.name),
                )
                + "?page={}".format(self.entry.link),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Shows page properties",
                static("{}/icons/icons8-download-96.png".format(LinkDatabase.name)),
            ),
        )

        buttons.append(
            EntryButton(
                self.user,
                "Scan",
                reverse(
                    "{}:entry-scan".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Scans entry for new links",
                static("{}/icons/icons8-radar-64.png".format(LinkDatabase.name)),
            ),
        )

        return buttons

    def get_view_menu_buttons(self):
        config = Configuration.get_object().config_entry
        buttons = []

        if self.entry.source_obj:
            buttons.append(
                EntryButton(
                    self.user,
                    "Source",
                    reverse(
                        "{}:source-detail".format(LinkDatabase.name),
                        args=[self.entry.source_obj.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Source: {}".format(self.entry.source_obj.title),
                ),
            )
        elif self.entry.source and self.entry.source != "":
            buttons.append(
                EntryButton(
                    self.user,
                    "Source",
                    self.entry.source,
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Source: {}".format(self.entry.source),
                ),
            )

        if self.entry.artist and self.entry.artist != "":
            buttons.append(
                EntryButton(
                    self.user,
                    self.entry.artist,
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
                    self.entry.album,
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=album+%3D+{}".format(self.entry.album),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Search for entries in {} album".format(self.entry.album),
                ),
            )

        if config.auto_store_domain_info and self.entry.domain_obj:
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
                ),
            )
        else:
            domain_url = HtmlPage(self.entry.link).get_domain()

            buttons.append(
                EntryButton(
                    self.user,
                    "Domain",
                    reverse(
                        "{}:entries-omni-search".format(LinkDatabase.name),
                    )
                    + "?search=link+%3D+{}".format(domain_url),
                    ConfigurationEntry.ACCESS_TYPE_ALL,
                    "Domain: {}".format(domain_url),
                ),
            )

        archive_link = self.entry.get_archive_link()
        buttons.append(
            EntryButton(
                self.user,
                "Archive.org",
                archive_link,
                ConfigurationEntry.ACCESS_TYPE_ALL,
                "Archive link: {}".format(archive_link),
                "https://archive.org/offshoot_assets/favicon.ico",
            ),
        )

        if config.link_save:
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
                    "https://archive.org/offshoot_assets/favicon.ico",
                ),
            )

        return buttons

    def get_advanced_menu_buttons(self):
        buttons = []

        buttons.append(
            EntryButton(
                self.user,
                "",
                reverse(
                    "{}:entry-remove".format(LinkDatabase.name),
                    args=[self.entry.id],
                ),
                ConfigurationEntry.ACCESS_TYPE_OWNER,
                "Removes entry: {}".format(self.entry.title),
                static("{}/icons/icons8-trash-100.png".format(LinkDatabase.name)),
            ),
        )

        if not self.entry.dead:
            buttons.append(
                EntryButton(
                    self.user,
                    "Dead",
                    reverse(
                        "{}:entry-dead".format(LinkDatabase.name),
                        args=[self.entry.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Marks entry as dead:{}".format(self.entry.title),
                ),
            )
        else:
            buttons.append(
                EntryButton(
                    self.user,
                    "Not dead",
                    reverse(
                        "{}:entry-not-dead".format(LinkDatabase.name),
                        args=[self.entry.id],
                    ),
                    ConfigurationEntry.ACCESS_TYPE_OWNER,
                    "Marks entry as not dead:{}".format(self.entry.title),
                ),
            )

        return buttons

    def get_parameters(self):
        parameters = []

        parameters.append(EntryParameter("Publish date", self.entry.date_published))

        if self.entry.user != "":
            parameters.append(EntryParameter("User", self.entry.user))
        if self.entry.status_code:
            parameters.append(EntryParameter("Status code", self.entry.status_code))

        parameters.append(EntryParameter("Vote", self.entry.get_vote()))
        parameters.append(EntryParameter("Language", self.entry.language))
        if self.entry.dead:
            parameters.append(EntryParameter("Dead", self.entry.dead))

        return parameters

    def get_frame_html(self):
        thumbnail = self.entry.get_thumbnail()
        if thumbnail:
            frame_text = """
            <div>
                <img src="{}" class="link-detail-thumbnail"/>
            </div>"""

            frame_text = frame_text.format(self.entry.get_thumbnail())
            return frame_text
        return ""

    def get_description_html(self):
        description = self.entry.description
        if not description or description == "":
            return ""

        from ..webtools import InputContent

        return """{}""".format(InputContent(description).htmlify())
