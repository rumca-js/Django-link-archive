class SearchEngine(object):
    def __init__(self, query_term=None, url=None):
        self.query_term = query_term
        self.url = url

    def get_name(self):
        return ""

    def get_title(self):
        return self.get_name()

    def get_address(self):
        return ""

    def get_search_address(self):
        return ""

    def get_search_argument(self):
        return "q"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term

        return "{}?{}={}".format(
            self.get_search_address(), self.get_search_argument(), search_term
        )


class SearchEngineWikipedia(SearchEngine):
    def get_name(self):
        return "Wikipedia"

    def get_search_address(self):
        return "https://en.wikipedia.org/w/index.php"

    def get_search_argument(self):
        return "search"


class SearchEngineDuckDuckGo(SearchEngine):
    def get_name(self):
        return "DuckDuckGo"

    def get_search_address(self):
        return "https://duckduckgo.com/"


class SearchEngineStartPage(SearchEngine):
    def get_name(self):
        return "StartPage"

    def get_search_address(self):
        return "https://www.startpage.com"


class SearchEngineGoogle(SearchEngine):
    def get_name(self):
        return "Google"

    def get_search_address(self):
        return "https://google.com/"


class SearchEngineGoogleCache(SearchEngine):
    """
    TODO Should not be registered, for normal search types
    """

    def get_name(self):
        return "GoogleCache"

    def get_search_address(self):
        return "https://webcache.googleusercontent.com"

    def get_search_string(self, search_term=None):
        """
        Search term needs to be URL

        TODO do we need this 27 in the search query?
        is this enough? [https://www.google.com/search?q=cache:seroundtable.com].
        """
        if not search_term:
            search_term = self.query_term
            if self.url:
                search_term = self.url

        if not search_term:
            return self.get_search_address()

        return "{}/{}{}".format(
            self.get_search_address(), "search?q=cache:", search_term
        )
        

class SearchEngineArchiveOrg(SearchEngine):

    def get_name(self):
        return "Archive.org"

    def get_search_address(self):
        return "https://web.archive.org"

    def get_search_string(self, search_term=None):
        """
        """
        from ..services.waybackmachine import WaybackMachine
        from ..dateutils import DateUtils

        if not search_term:
            search_term = self.query_term
            if self.url:
                search_term = self.url

        if not search_term:
            return self.get_search_address()

        m = WaybackMachine()
        formatted_date = m.get_formatted_date(DateUtils.get_datetime_now_utc())
        archive_link = m.get_archive_url_for_date(formatted_date, search_term)
        return archive_link


class SearchEngineBing(SearchEngine):
    def get_name(self):
        return "Bing"

    def get_search_address(self):
        return "https://bing.com/"


class SearchEngineKagi(SearchEngine):
    def get_name(self):
        return "Kagi"

    def get_search_address(self):
        return "https://kagi.com/search"


class SearchEngineReddit(SearchEngine):
    def get_name(self):
        return "Reddit"

    def get_search_address(self):
        return "https://www.reddit.com/search/"


class SearchEngineQuora(SearchEngine):
    def get_name(self):
        return "Quora"

    def get_search_address(self):
        return "https://www.quora.com/search"


class SearchEnginePerplexity(SearchEngine):
    def get_name(self):
        return "Perplexity.ai"

    def get_search_address(self):
        return "https://www.perplexity.ai/"


class SearchEngineWolfram(SearchEngine):
    def get_name(self):
        return "Wolfram"

    def get_search_address(self):
        return "https://www.wolframalpha.com/input"

    def get_search_argument(self):
        return "i"


class SearchEngineYewTube(SearchEngine):
    def get_name(self):
        return "Yew.tube"

    def get_search_address(self):
        return "https://yewtu.be/search"


class SearchEngineStackOverFlow(SearchEngine):
    def get_name(self):
        return "StackOverFlow"

    def get_search_address(self):
        return "https://stackoverflow.com/search"


class SearchEngineYouTube(SearchEngine):
    def get_name(self):
        return "YouTube"

    def get_search_address(self):
        return "https://www.youtube.com/results"

    def get_search_argument(self):
        return "search_query"


class SearchEngineSpotify(SearchEngine):
    def get_name(self):
        return "Spotify"

    def get_search_address(self):
        return "https://open.spotify.com/search"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "{}/{}".format(self.get_search_address(), search_term)


class SearchEngineOdysee(SearchEngine):
    def get_name(self):
        return "Odysee"

    def get_search_address(self):
        return "https://odysee.com/$/search"


class SearchEngineTikTok(SearchEngine):
    def get_name(self):
        return "TikTok"

    def get_search_address(self):
        return "https://www.tiktok.com/search"


class SearchEngineMarginalia(SearchEngine):
    def get_name(self):
        return "Marginalia"

    def get_search_address(self):
        return "https://search.marginalia.nu/search"

    def get_search_argument(self):
        return "query"


class SearchEngineChatOpenAI(SearchEngine):
    def get_name(self):
        return "ChatGPT"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "https://chat.openai.com/"


class SearchEngineBard(SearchEngine):
    def get_name(self):
        return "Bard"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "https://bard.google.com/"


class SearchEngineHnAlgolia(SearchEngine):
    def get_name(self):
        return "HackerNews - Algolia"

    def get_search_address(self):
        return "https://hn.algolia.com/"

    def get_search_argument(self):
        return "query"


class SearchEngineRumble(SearchEngine):
    def get_name(self):
        return "Rumble"

    def get_search_address(self):
        return "https://rumble.com/search/all"


class SearchEngineWhoogle(SearchEngine):
    def get_name(self):
        return "Whoogle"

    def get_search_address(self):
        return "https://whoogle.io/search"


class SearchEngineMwmbl(SearchEngine):
    def get_name(self):
        return "Mwmbl"

    def get_search_address(self):
        return "https://mwmbl.org/"


class SearchEngineSubstack(SearchEngine):
    def get_name(self):
        return "Substack"

    def get_search_address(self):
        return "https://substack.com/search/test"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "{}/{}".format(self.get_search_address(), search_term)


class SearchEngines(object):
    def __init__(self, search_term=None, url=None):
        self.search_term = search_term
        self.url = url

    def get_search_engines():
        # fmt: off
        return [
            # search engines
            SearchEngineGoogle,
            SearchEngineDuckDuckGo,
            SearchEngineBing,
            SearchEngineKagi,
            SearchEngineStartPage,
            SearchEngineMwmbl,
            SearchEngineWikipedia,
            SearchEngineWolfram,
            SearchEngineWhoogle,
            SearchEngineMarginalia,

            # library searches
            SearchEngineGoogleCache,
            SearchEngineArchiveOrg,

            # Audio Video
            SearchEngineYouTube,
            SearchEngineSpotify,
            SearchEngineTikTok,
            SearchEngineRumble,
            SearchEngineYewTube,
            SearchEngineOdysee,

            # Social media
            SearchEngineReddit,
            SearchEngineSubstack,
            SearchEngineStackOverFlow,
            SearchEngineQuora,
            SearchEngineHnAlgolia,

            # AI
            SearchEngineChatOpenAI,
            SearchEngineBard,
            SearchEnginePerplexity,
        ]
        # fmt: on

    def get(self):
        engine_classes = SearchEngines.get_search_engines()

        result = []
        for engine_class in engine_classes:
            engine_object = engine_class(self.search_term, self.url)

            result.append(engine_object)

        return result
