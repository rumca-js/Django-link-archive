from ..webtools import (
   RedditUrlHandler,
   GitHubUrlHandler,
)
from .fakeinternet import FakeInternetTestCase, MockRequestCounter, YouTubeJsonHandlerMock


class RedditUrlHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_constructor(self):
        test_link = "https://www.reddit.com/r/redditdev/comments/1hw8p3j/i_used_the_reddit_api_to_save_myself_time_with_my/"

        handler = RedditUrlHandler(test_link)

        data = handler.get_json_data()

        self.assertIn("upvote_ratio", data)


class GitHubUrlHandlerTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_constructor(self):
        test_link = "https://api.github.com/repos/rumca-js/Django-link-archive"

        handler = GitHubUrlHandler(test_link)

        data = handler.get_json_data()

        self.assertIn("thumbs_up", data)
