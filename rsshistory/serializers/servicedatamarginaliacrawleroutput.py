"""
https://downloads.marginalia.nu/

 - Find a downloadable file
 - it is tarball
 - extract it
 - copy contents of 'crawler.log'
"""


class MarginaliaCrawlerOutput(object):
    def __init__(self, contents):
        self.contents = contents

    def get_links(self):
        links = []

        lines = self.contents.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                link = self.get_processed_link(line)
                if link:
                    links.append(link)

        return links

    def get_processed_link(self, line):
        wh = line.find(" ")
        if wh >= 0:
            return line[:wh]
