from bs4 import BeautifulSoup
import re


class InputContent(object):
    def __init__(self, text):
        self.text = text

    def htmlify(self):
        """
        Use iterative approach. There is one thing to keep in mind:
         - text can contain <a href=" links already

        So some links needs to be translated. Some do not.

        @return text with https links changed into real links
        """
        self.text = self.strip_html_attributes()
        self.text = self.linkify("https://")
        self.text = self.linkify("http://")
        return self.text

    def strip_html_attrs(self):
        soup = BeautifulSoup(self.text, "html.parser")

        for tag in soup.find_all(True):
            if tag.name == "a":
                # Preserve "href" attribute for anchor tags
                tag.attrs = {"href": tag.get("href")}
            elif tag.name == "img":
                # Preserve "src" attribute for image tags
                tag.attrs = {"src": tag.get("src")}
            else:
                # Remove all other attributes
                tag.attrs = {}

        self.text = str(soup)
        return self.text

    def linkify(self, protocol="https://"):
        """
        @return text with https links changed into real links
        """
        if self.text.find(protocol) == -1:
            return self.text

        result = ""
        i = 0

        while i < len(self.text):
            pattern = r"{}\S+(?![\w.])".format(protocol)
            match = re.match(pattern, self.text[i:])
            if match:
                url = match.group()
                # Check the previous 10 characters
                preceding_chars = self.text[max(0, i - 10) : i]

                # We do not care who write links using different char order
                if '<a href="' not in preceding_chars and "<img" not in preceding_chars:
                    result += f'<a href="{url}">{url}</a>'
                else:
                    result += url
                i += len(url)
            else:
                result += self.text[i]
                i += 1

        self.text = result

        return result
