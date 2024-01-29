class SearchEngine(object):
    def __init__(self, query_term=None):
        self.query_term = query_term

    def get_name(self):
        return ""

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


class SearchEngineGoogle(SearchEngine):
    def get_name(self):
        return "Google"

    def get_search_address(self):
        return "https://google.com/"


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
    def __init__(self, search_term=None):
        self.search_term = search_term

    def get_search_engines():
        return [
            SearchEngineWikipedia,
            SearchEngineGoogle,
            SearchEngineDuckDuckGo,
            SearchEngineBing,
            SearchEngineKagi,
            SearchEngineHnAlgolia,
            SearchEngineReddit,
            SearchEngineQuora,
            SearchEnginePerplexity,
            SearchEngineWolfram,
            SearchEngineYewTube,
            SearchEngineStackOverFlow,
            SearchEngineYouTube,
            SearchEngineSpotify,
            SearchEngineOdysee,
            SearchEngineTikTok,
            SearchEngineMarginalia,
            SearchEngineChatOpenAI,
            SearchEngineRumble,
            SearchEngineWhoogle,
            SearchEngineSubstack,
        ]

    def get(self):
        engine_classes = SearchEngines.get_search_engines()

        result = []
        for engine_class in engine_classes:
            engine_object = engine_class(self.search_term)

            result.append(engine_object)

        return result
