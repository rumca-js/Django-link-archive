

def get_page(url):
    import urllib.request, urllib.error, urllib.parse
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        webContent = urllib.request.urlopen(req).read().decode('UTF-8')
        return webContent
    except Exception as e:
       logging.critical(e, exc_info=True) 


import re
import requests
def parse_all_links(domain, html):
    links = re.findall(domain)
    #    for e in links:
    #        print(e)

    #links = re.findall(r"""a href=(['"].*['"])""", html)  # find links starting with href
    #print("found the following links addresses: ".format(len(html)))  # print a message before the output

    #if len(links) == 0:
    #    print("Sorry, no links found")
    #else:
    #    count = 0  # this count how many links are displayed
    #    for e in links:
    #        print(e)
    #        count += 1

    #print('--------------\nCount:{}'.format(count))


parse_all_links("http://www.onet.pl", requests.get("http://www.onet.pl").text)
