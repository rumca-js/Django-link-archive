from ..services import GoogleTranslate
from .fakeinternet import FakeInternetTestCase


class GoogleTranslateTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_translate(self):
        p = GoogleTranslate("https://www-youtube.com/test?parameter=True")

        # call tested function
        url = p.get_translate_url()

        self.assertEqual(
            url,
            "https://www--youtube-com.translate.goog/test?_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en&_x_tr_pto=wapp&parameter=True",
        )
