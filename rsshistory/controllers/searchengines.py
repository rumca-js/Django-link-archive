import urllib.parse
from utils.dateutils import DateUtils


class SearchEngine(object):
    def __init__(self, query_term=None, url=None):
        self.query_term = query_term
        self.url = url

    def get_name(self):
        return ""

    def get_title(self):
        return self.get_name()

    def get_description(self):
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

    def get_address(self):
        return "https://en.wikipedia.org"

    def get_search_address(self):
        return "https://en.wikipedia.org/w/index.php"

    def get_search_argument(self):
        return "search"


class SearchEngineDuckDuckGo(SearchEngine):
    def get_name(self):
        return "DuckDuckGo"

    def get_address(self):
        return "https://duckduckgo.com"

    def get_search_address(self):
        return "https://duckduckgo.com/"


class SearchEngineStartPage(SearchEngine):
    def get_name(self):
        return "StartPage"

    def get_address(self):
        return "https://www.startpage.com"

    def get_search_address(self):
        return "https://www.startpage.com"


class SearchEngineGoogle(SearchEngine):
    def get_name(self):
        return "Google"

    def get_address(self):
        return "https://google.com"

    def get_search_address(self):
        return "https://google.com/search"


class SearchEngineGoogleCache(SearchEngine):
    def get_name(self):
        return "GoogleCache"

    def get_address(self):
        return "http://webcache.googleusercontent.com"

    def get_search_address(self):
        return "http://webcache.googleusercontent.com/search"

    def get_search_argument(self):
        return "q"

    def encode_url(self, url):
        return urllib.parse.quote(url)

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term

        return "{}?{}=cache:{}".format(
            self.get_search_address(),
            self.get_search_argument(),
            self.encode_url(search_term),
        )


class SearchEngineBing(SearchEngine):
    def get_name(self):
        return "Bing"

    def get_address(self):
        return "https://bing.com"

    def get_search_address(self):
        return "https://bing.com/"


class SearchEngineKagi(SearchEngine):
    def get_name(self):
        return "Kagi"

    def get_address(self):
        return "https://kagi.com"

    def get_search_address(self):
        return "https://kagi.com/search"


class SearchEnginePerplexity(SearchEngine):
    def get_name(self):
        return "Perplexity.ai"

    def get_address(self):
        return "https://www.perplexity.ai"

    def get_search_address(self):
        return "https://www.perplexity.ai/"


class SearchEngineWolfram(SearchEngine):
    def get_name(self):
        return "Wolfram"

    def get_address(self):
        return "https://www.wolframalpha.com"

    def get_search_address(self):
        return "https://www.wolframalpha.com/input"

    def get_search_argument(self):
        return "i"


class SearchEngineMwmbl(SearchEngine):
    def get_name(self):
        return "Mwmbl"

    def get_address(self):
        return "https://mwmbl.org"

    def get_search_address(self):
        return "https://mwmbl.org/"


class SearchEngineWhoogle(SearchEngine):
    def get_name(self):
        return "Whoogle"

    def get_address(self):
        return "https://whoogle.io"

    def get_search_address(self):
        return "https://whoogle.io/search"


class SearchEngineMarginalia(SearchEngine):
    def get_name(self):
        return "Marginalia"

    def get_address(self):
        return "https://search.marginalia.nu"

    def get_search_address(self):
        return "https://search.marginalia.nu/search"

    def get_search_argument(self):
        return "query"


class SearchEngineYahoo(SearchEngine):
    def get_name(self):
        return "Yahoo"

    def get_address(self):
        return "https://yahoo.com"


class SearchEngineBaidu(SearchEngine):
    def get_name(self):
        return "Baidu"

    def get_description(self):
        return "Chinese"

    def get_address(self):
        return "https://baidu.com"


class SearchEngineYandex(SearchEngine):
    def get_name(self):
        return "Yandex"

    def get_description(self):
        return "Russian"

    def get_address(self):
        return "https://yandex.com"


class SearchEngineBrave(SearchEngine):
    def get_name(self):
        return "Brave"

    def get_address(self):
        return "https://search.brave.com"


class SearchEngineMojeek(SearchEngine):
    def get_name(self):
        return "Mojeek"

    def get_address(self):
        return "https://mojeek.com"


class SearchEngineMorphic(SearchEngine):
    def get_name(self):
        return "Morphic"

    def get_address(self):
        return "https://morphic.sh"


class SearchEngineShodan(SearchEngine):
    def get_name(self):
        return "Shodan"

    def get_address(self):
        return "https://shodan.io"


class SearchEngineSogou(SearchEngine):
    def get_name(self):
        return "Sogou"

    def get_address(self):
        return "https://sogou.com"

    def get_description(self):
        return "Chinese"


class SearchEngineStract(SearchEngine):
    def get_name(self):
        return "Stract"

    def get_address(self):
        return "https://stract.com"


class SearchEngineWiby(SearchEngine):
    def get_name(self):
        return "Wiby"

    def get_address(self):
        return "https://wiby.me"


class SearchEngineCSE(SearchEngine):
    def get_name(self):
        return "Programmable Google Search Engine"

    def get_address(self):
        return "https://cse.google.com"


class SearchEngineAnoox(SearchEngine):
    def get_name(self):
        return "Anoox"

    def get_address(self):
        return "https://anoox.com"


class SearchEngineGreppr(SearchEngine):
    def get_name(self):
        return "Greppr"

    def get_address(self):
        return "https://greppr.org"


class SearchEngineLetsearch(SearchEngine):
    def get_name(self):
        return "Letsearch.ru"

    def get_description(self):
        return "Russian"

    def get_address(self):
        return "https://letsearch.ru"


class SearchEnginePresearch(SearchEngine):
    def get_name(self):
        return "Presearch"

    def get_address(self):
        return "https://presearch.io"


# ------ Archive libraries


class SearchEngineArchiveOrg(SearchEngine):
    def get_name(self):
        return "Archive.org"

    def get_address(self):
        return "https://web.archive.org"

    def get_search_address(self):
        return "https://web.archive.org"

    def get_search_string(self, search_term=None):
        """ """
        from utils.services.waybackmachine import WaybackMachine

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


class SearchEngineArchivePh(SearchEngine):
    def get_name(self):
        return "archive.ph"

    def get_address(self):
        return "https://archive.ph"

    def get_search_address(self):
        return "https://archive.ph"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
            if self.url:
                search_term = self.url

        if not search_term:
            return self.get_search_address()

        return "{}/{}".format(self.get_search_address(), "search?q=cache:", search_term)


class SearchEngineAnnasArchive(SearchEngine):
    def get_name(self):
        return "Anna's Archive"

    def get_address(self):
        return "https://annas-archive.org"

    def get_search_address(self):
        return "https://annas-archive.org"


# ------ Audio video streaming


class SearchEngineYewTube(SearchEngine):
    def get_name(self):
        return "Yew.tube"

    def get_address(self):
        return "https://yewtu.be"

    def get_search_address(self):
        return "https://yewtu.be/search"


class SearchEngineGitHub(SearchEngine):
    def get_name(self):
        return "GitHub"

    def get_address(self):
        return "https://github.com"

    def get_search_address(self):
        return "https://github.com/search"

    def get_search_string(self, search_term=None):
        data = super().get_search_string(search_term)
        data = data + "&type=repositories"
        return data


class SearchEngineYouTube(SearchEngine):
    def get_name(self):
        return "YouTube"

    def get_address(self):
        return "https://www.youtube.com"

    def get_search_address(self):
        return "https://www.youtube.com/results"

    def get_search_argument(self):
        return "search_query"


class SearchEngineSpotify(SearchEngine):
    def get_name(self):
        return "Spotify"

    def get_address(self):
        return "https://open.spotify.com"

    def get_search_address(self):
        return "https://open.spotify.com/search"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "{}/{}".format(self.get_search_address(), search_term)


class SearchEngineOdysee(SearchEngine):
    def get_name(self):
        return "Odysee"

    def get_address(self):
        return "https://odysee.com"

    def get_search_address(self):
        return "https://odysee.com/$/search"


class SearchEngineTikTok(SearchEngine):
    def get_name(self):
        return "TikTok"

    def get_address(self):
        return "https://www.tiktok.com"

    def get_search_address(self):
        return "https://www.tiktok.com/search"


class SearchEngineRumble(SearchEngine):
    def get_name(self):
        return "Rumble"

    def get_address(self):
        return "https://rumble.com"

    def get_search_address(self):
        return "https://rumble.com/search/all"


# ------ Social media


class SearchEngineReddit(SearchEngine):
    def get_name(self):
        return "Reddit"

    def get_address(self):
        return "https://www.reddit.com"

    def get_search_address(self):
        return "https://www.reddit.com/search/"


class SearchEngineQuora(SearchEngine):
    def get_name(self):
        return "Quora"

    def get_address(self):
        return "https://www.quora.com"

    def get_search_address(self):
        return "https://www.quora.com/search"


class SearchEngineSubstack(SearchEngine):
    def get_name(self):
        return "Substack"

    def get_address(self):
        return "https://substack.com"

    def get_search_address(self):
        return "https://substack.com/search/test"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "{}/{}".format(self.get_search_address(), search_term)


class SearchEngineStackOverFlow(SearchEngine):
    def get_name(self):
        return "StackOverFlow"

    def get_address(self):
        return "https://stackoverflow.com"

    def get_search_address(self):
        return "https://stackoverflow.com/search"


class SearchEngineHnAlgolia(SearchEngine):
    def get_name(self):
        return "HackerNews - Algolia"

    def get_address(self):
        return "https://hn.algolia.com"

    def get_search_address(self):
        return "https://hn.algolia.com/"

    def get_search_argument(self):
        return "query"


# -- AI chat bots


class SearchEngineChatOpenAI(SearchEngine):
    def get_name(self):
        return "ChatGPT"

    def get_address(self):
        return "https://chatgpt.com"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "https://chat.openai.com/"


class SearchEngineBard(SearchEngine):
    def get_name(self):
        return "Bard"

    def get_address(self):
        return "https://bard.google.com"

    def get_search_string(self, search_term=None):
        if not search_term:
            search_term = self.query_term
        return "https://bard.google.com/"


class SearchEngines(object):
    def __init__(self, search_term=None, url=None):
        self.search_term = search_term
        self.url = url

    def get(self):
        engine_classes = SearchEngines.get_searchable_places()

        result = []
        for engine_class in engine_classes:
            engine_object = engine_class(self.search_term, self.url)

            result.append(engine_object)

        return result

    def get_searchable_places():
        result = []
        result.extend(SearchEngines.get_search_engines())
        result.extend(SearchEngines.get_aibots())
        result.extend(SearchEngines.get_streaming())
        result.extend(SearchEngines.get_social_media())
        result.extend(SearchEngines.get_archive_libraries())

        return result

    def get_gateways():
        result = []

        result.extend(SearchEngines.get_streaming())
        result.extend(SearchEngines.get_social_media())

        # TODO add to containers
        # https://lobste.rs/
        # result.append("https://news.ycombinator.com")
        # result.append("https://medium.com")
        # result.append("https://mastodon.social/explore")
        # result.append("https://join-lemmy.org/instances")
        # result.append("https://joinpeertube.org")
        # result.append("https://facebook.com")
        # result.append("https://amazon.com")

        return result

    def get_search_engines():
        # fmt: off
        return [
            # search engines
            SearchEngineGoogle,
            SearchEngineCSE,
            SearchEngineDuckDuckGo,
            SearchEngineBing,
            SearchEngineYahoo,
            SearchEngineKagi,
            SearchEngineBrave,
            SearchEngineStartPage,
            SearchEnginePresearch,
            SearchEngineMwmbl,
            SearchEngineWolfram,
            SearchEngineWhoogle,
            SearchEngineMarginalia,
            SearchEngineWiby,
            SearchEngineShodan,
            SearchEngineSogou,
            SearchEngineBaidu,
            SearchEngineYandex,
            SearchEngineLetsearch,
            SearchEngineMojeek,
            SearchEngineMorphic,
            SearchEngineStract,
            SearchEngineAnoox,
            SearchEngineGreppr,
        ]
        # fmt: on

    def get_aibots():
        # fmt: off
        return [
            SearchEngineChatOpenAI,
            SearchEngineBard,
            SearchEnginePerplexity,
        ]
        # fmt: on

    def get_streaming():
        # fmt: off
        return [
            SearchEngineYouTube,
            SearchEngineSpotify,
            SearchEngineTikTok,
            SearchEngineRumble,
            SearchEngineYewTube,
            SearchEngineOdysee,
        ]
        # fmt: on

    def get_social_media():
        # fmt: off
        return [
            SearchEngineGitHub,
            SearchEngineReddit,
            SearchEngineSubstack,
            SearchEngineStackOverFlow,
            SearchEngineQuora,
            SearchEngineHnAlgolia,
        ]
        # fmt: on

    def get_archive_libraries():
        # fmt: off
        return [
            SearchEngineArchiveOrg,
            SearchEngineArchivePh,
            SearchEngineWikipedia,
            SearchEngineAnnasArchive,
        ]
        # fmt: on
