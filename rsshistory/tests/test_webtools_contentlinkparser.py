from webtools import ContentLinkParser

from .fakeinternet import FakeInternetTestCase


contents_with_links = """
<!DOCTYPE html>
<html lang="en-US">
	<head>
		<meta charSet="utf-8"/>
        "09 jan. 2024 02:00"
    </head>
    <body>
      <a href="https://www.youtube.com">YouTube domain</a>
      <a href="https://www.youtube.com:443">YouTube domain with port</a>
      <a href="https://www.youtube.com:443/location">YouTube domain with port, and location</a>
      <a href="https://www.youtube.com/location">YouTube domain, and location</a>
      <a href="https://www.youtube.com/location?v=12323&test=q#whatever">YouTube domain, and location</a>
      <a href="https://linkedin.com/location">Linkedin with location</a>
      <a href="//test.com/location">Test.com with location</a>
      <a href="/location">This page with location</a>
      <a href="location">This page with location</a>
      <a href="https:&#x2F;&#x2F;www.cedarpolicy.com" rel="nofollow">https:&#x2F;&#x2F;www.cedarpolicy.com</a>
      <a href="mailto:renegat@renegat0x0.ddns.net">Mailto</a>
    </body>
</html>
"""


class ContentLinkParserTest(FakeInternetTestCase):
    def test_get_links(self):
        p = ContentLinkParser(
            "https://test_get_links.com/test",
            contents_with_links,
        )

        links = p.get_links()
        print(links)

        self.assertTrue("https://www.youtube.com" in links)
        self.assertTrue("https://www.youtube.com:443" in links)
        self.assertTrue("https://www.youtube.com:443/location" in links)
        self.assertTrue("https://www.youtube.com/location" in links)
        self.assertTrue(
            "https://www.youtube.com/location?v=12323&test=q#whatever" in links
        )
        self.assertTrue("https://test.com/location" in links)
        self.assertTrue("https://test_get_links.com/location" in links)
        self.assertTrue("https://test_get_links.com/test/location" in links)
        self.assertTrue("https://renegat0x0.ddns.net" in links)
        self.assertTrue("https://www.cedarpolicy.com" in links)

    def test_get_domains(self):
        p = ContentLinkParser(
            "https://test_get_links.com/test",
            contents_with_links,
        )

        domains = p.get_domains()
        print(domains)

        self.assertTrue("https://www.youtube.com" in domains)
        self.assertTrue("https://test.com" in domains)
        self.assertTrue("https://test_get_links.com" in domains)
        self.assertTrue("https://www.youtube.com:443" not in domains)
        self.assertTrue("https://renegat0x0.ddns.net" in domains)
        self.assertTrue("https://www.cedarpolicy.com" in domains)
