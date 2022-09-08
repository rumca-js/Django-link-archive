
import logging



import re
import requests
class WebLinkParser(object):

    def __init__(self, url, searchplace = None):
        self.domain = url

        if searchplace:
            self.searchplace = searchplace
        else:
            self.searchplace = self.domain

        self.exclude_list = set()
        self.limit_to_domain = False

    def parse_full_links(self, html = None):
        if html == None: 
            html = self.get_page(self.searchplace)

        searchstring = "https://"
        links = set()

        wh = 1
        while wh:
            wh2 = html.find(searchstring, wh)

            where = set()
            where.add(html.find("\"", wh2+1))
            where.add(html.find("}", wh2+1))
            where.add(html.find("<", wh2+1))
            where.add(html.find(">", wh2+1))
            where.add(html.find("\\", wh2+1))
            where.add(html.find(")", wh2+1))
            where.add(html.find("(", wh2+1))
            where.discard(-1)
            val = min(where)

            foundstring = html[wh2: val]

            if foundstring != searchstring:
                links.add(foundstring)

            if wh2 == -1:
                break

            wh = wh2 + 1

        return links

    import re
    import requests
    def parse_a_hrefs(self):
        links = set()

        page = self.get_page(self.searchplace)

        wh = 1
        while wh:
            wh = page.find('<a href="', wh + 1)

            if wh > 0:
                #print(wh)
                text = self.extract_html(page, '<a href="', '"', wh)
                if text:
                    links.add(text)
                #print(text)
            else:
                break

        return links

    def parse_links_and_titles(self):
        links_and_titles = []

        links = self.parse_full_links()
        links.update( self.parse_a_hrefs())

        links = self.process_links(links)

        for link in links:
            if not self.check_string(link):
                continue

            print("Reading link {0}".format(link))

            text = self.get_page(link)
            if not text:
                continue

            title = self.extract_html(text, "<title>", "</title>")

            if title:
                links_and_titles.append( (title, link) )

        return links_and_titles

    def get_page(self, url):
        import urllib.request, urllib.error, urllib.parse
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            webContent = urllib.request.urlopen(req).read().decode('UTF-8')
            return webContent
        except Exception as e:
           logging.critical(e, exc_info=True) 

    def check_string(self, found_string):
        if found_string.find(self.domain) != 0:
            return False

        ask = found_string.find("?")
        if ask != -1:
            found_string = found_string[:ask]

        for item in self.exclude_list:
            if found_string.endswith(item):
                return False

        return True

    def process_links(self, links):
        result = set()
        for link in links:
            if link.startswith("/"):
                result.add(self.domain + link)
            else:
                result.add(link)
        return result

    def exclude(self, ext):
        self.exclude_list.add(ext)

    def extract_html(self, text, tag, closingtag, wh = None):
        if not wh:
            wh = 0

        wh = text.find(tag, wh)

        if wh > 0:
            wh2 = text.find(closingtag, len(tag) + wh + 1)

            if wh2 > 0:
                title = text[wh + len(tag):wh2]
                if title.strip() != "":
                    return title

    def exclude_default(self):
        self.exclude(".jpg")
        self.exclude(".jpeg")
        self.exclude(".js")
        self.exclude(".css")
        self.exclude(".svg")
        self.exclude(".png")



domain = "http://www.onet.pl"

domain = "https://www.louderwithcrowder.com"
searchdomain = "https://www.louderwithcrowder.com/posts"

#domain = "https://niezalezna.pl"
#searchdomain = "https://niezalezna.pl"

parser = WebLinkParser(domain, searchdomain)
parser.exclude_default()
parser.limit_to_domain = True
#links = parser.parse_full_links()

links_data = parser.parse_links_and_titles()

#text = get_page(domain)
#text = requests.get("http://www.onet.pl").text
#links = parse_full_links(domain, text)

for link_data in links_data:
    print("'{0}' '{1}'".format(link_data[0], link_data[1]))
