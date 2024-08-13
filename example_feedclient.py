"""
This is example script about how to use this project as a simple RSS reader
"""
import socket
import json
import traceback
import argparse
from sqlmodel import SqlModel


from rsshistory.webtools import (
    PageOptions,
    WebConfig,
    WebLogger,
    PrintWebLogger,
    Url,
    HttpPageHandler,
)


sources = [
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCXGgrKt94gR6lmN4aN3mYTg", "title" : "austin evans"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCyl5V3-J_Bsy3x-EBCJwepg", "title" : "babylon bee"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCmrLCXSDScliR7q8AxxjvXg", "title" : "black pidgeon speaks"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC7vVhkEfw4nOGp8TyDk7RcQ", "title" : "boston dynamics"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UClozNP-QPyVatzpGKC25s0A", "title" : "brad colbow"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCld68syR8Wi-GY_n4CaoJGA", "title" : "brodie robertson"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCROQqK3_z79JuTetNP3pIXQ", "title" : "captain midnight"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCtinbF-Q-fVthA0qrFQTgXQ", "title" : "casey"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCxHAlbZQNFU2LgEtiqd2Maw", "title" : "c++ weekly with jason turner"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCLLO-H4NQXNa_DhUv-rqN9g", "title" : "cd action"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCPKT_csvP72boVX0XrMtagQ", "title" : "cercle"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCwjvvgGX6oby5mZ3gbDe8Ug", "title" : "china insights"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCgFP46yVT-GG4o1TgXn-04Q", "title" : "china uncensored"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCg6gPGh8HU2U01vaFCAsvmQ", "title" : "christ titus tech"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCFQMnBA3CS502aghlcr0_aw", "title" : "cofeezilla"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCX_t3BvnQtS5IHzto_y7tbw", "title" : "coreteks"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC4QZ_LsYcvcq7qOsOhpAX4A", "title" : "coldfusion"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC9Ntx-EF3LzKY1nQ5rTUP2g", "title" : "cyriak"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCVls1GmFKf6WlTraIb_IaJg", "title" : "distrotube"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCTSRIY3GLFYIpkR2QwyeklA", "title" : "drew gooden"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCD4EOyXKjfDUhCI6jlOZZYQ", "title" : "eli the computer guy"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCCDGVMGoT8ql8JQLJt715jA", "title" : "emzdanowicz"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCDNHPNeWScAC8h8IxtEBtkQ", "title" : "eons of battle"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC_0CVCfC_3iuHqmyClu59Uw", "title" : "eta prime"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCO7fujFV_MuxTM0TuZrnE6Q", "title" : "felix colgrave"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCG_nvdTLdijiAAuPKxtvBjA", "title" : "filmento"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCNnKprAG-MWLsk-GsbsC2BA", "title" : "flashgitz"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCyNtlmLB73-7gtlBz00XOQQ", "title" : "folding ideas"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC2WHjPDvbE6O328n17ZGcfg", "title" : "forrest knight"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCRG_N2uO405WO4P3Ruef9NA", "title" : "friday checkout"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCHDxYLv8iovIbhrfl16CNyg", "title" : "gamelinked"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCNvzD7Z-g64bPXxGzaQaa4g", "title" : "gameranx"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCbu2SsF-Or3Rsn3NxqODImw", "title" : "gamespot"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCXa_bzvv7Oo1glaW9FldDhQ", "title" : "gaming bolt"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCmEbe0XH51CI09gm_9Fcn8Q", "title" : "glass reflection"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCkPjHTuNd_ycm__29dXM3Nw", "title" : "gf darwin"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCR-DXc1voovS8nhAvccRZhg", "title" : "jeff gerling"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCoOjH8D2XAgjzQlneM2W0EQ", "title" : "jake tran"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC7v3-2K1N84V67IF-WTRG-Q", "title" : "jeremy jahns"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC-2YHgc363EdcusLIBbgxzg", "title" : "joe scott"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCVIFCOJwv3emlVmBbPCZrvw", "title" : "joel havier"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCmGSJVG3mCRXVOP4yZrU1Dw", "title" : "john harris"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC337i8LcUSM4UMbLf820I8Q", "title" : "just some guy"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCLRlryMfL8ffxzrtqv0_k_w", "title" : "kino check"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCG2kQBVlgG7kOigXZTcKrQw", "title" : "kolem sie toczy"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC2_KC8lshtCyiLApy27raYw", "title" : "knowledgehusk"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCLr4hMhk_2KE0GUBSBrspGA", "title" : "kuba klawiter"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCJKt_QVDyUbqdm3ag_py2eQ", "title" : "kuokka77"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCtVGGeUqfVHOK4Q6nAwYO3g", "title" : "laterclips"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw", "title" : "linus tech tips"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCl2mFZoRqjw_ELax4Yisf6w", "title" : "louis rossman"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC2eYFnH61tmytImy1mTYvhA", "title" : "luke smith"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UClOGLGPOqlAiLmOvXW5lKbw", "title" : "mandalore gaming"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCBJycsmduvYEL83R_U4JriQ", "title" : "marques brownlee"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCTTZqMWBvLsUYqYwKTdjvkw", "title" : "mateusz chrobok"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCjuKQCmKlCtrPL2wl1uIphQ", "title" : "more pegasus"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC5T0tXJN5CrMZUEJuz4oovw", "title" : "nerdrotic"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCe6nK69Yc1zna7QSJEfA9pw", "title" : "niebezpiecznik"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCittVh8imKanO_5KohzDbpg", "title" : "paul joseph watson"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCswH8ovgUp5Bdg-0_JTYFNw", "title" : "russel brand"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCh9IfI45mmk59eDvSWtuuhQ", "title" : "ryan george"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCzKFvBRI6VT3jYJq6a820nA", "title" : "ryan long"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCA3-nIYWu4PTWkb6NwhEpzg", "title" : "ryan reynolds"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCyseFvMP4mZVlU5iEEbAamA", "title" : "salvatore ganacci"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCd6vEDS3SOhWbXZrxbrf_bw", "title" : "samtime"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCEq_Dr1GHvnNPQNfgOzhZ8Q", "title" : "solid jj"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCD6VugMZKRhSyzWEWA9W2fg", "title" : "sssethtzeentach"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCDvZTWvHZPTxJ4K1yTD2a1g", "title" : "squidmar miniatures"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UC2CKTY1TXQ4YQ3AHvyCgtbQ", "title" : "tabletop miniatures"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCtZO3K2p8mqFwiKWb9k7fXA", "title" : "techaltar"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCeeFfhMcJa1kjtfZAGskOCA", "title" : "techlinked"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCSJPFQdZwrOutnmSFYtbstA", "title" : "the critical drinker"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCjr2bPAyPV7t35MvcgT3W8Q", "title" : "the hated one"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCDVb4m_5QHhZElT47E1oODg", "title" : "dave cullen show"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCSbdMXOI_3HGiFviLZO6kNA", "title" : "thrillseeker"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCQSpnDG3YsFNf5-qHocF-WQ", "title" : "thiojoe"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCRlICXvO4XR4HMeEB9JjDlA", "title" : "thoughty2"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCxt2r57cLastdmrReiQJkEg", "title" : "tom nicolas"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCBa659QWEk1AI4Tg--mrJ2A", "title" : "tom scott"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCFLwN7vRu8M057qJF8TsBaA", "title" : "up is not down"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCvg_4SPPEZ7y4pk_iB7z6sw", "title" : "whimsu"},
        {"url" : "https://www.youtube.com/feeds/videos.xml?channel_id=UCxXu9tCU63mF1ntk89XPkzA", "title" : "worthkids"},
       # {"url" : "https://www.warhammer-community.com/feed", "title" : "Warhammer community"},
]


def read_source(source):
    result = []

    source_url = source["url"]
    source_title = source["title"]

    options = PageOptions()
    options.use_headless_browser = False
    options.use_full_browser = False

    url = Url(url = source_url, page_options = options)
    handler = url.get_handler()
    response = url.get_response()

    if response:
        for item in handler.get_entries():
            item["source"] = source_url
            item["source_title"] = source_title
            result.append(item)

    return result


class HtmlWriter(object):
    def __init__(self, file_name, conn):
        self.file_name = file_name
        self.conn = conn

    def write(self):
        rows = self.conn.select_all()

        complete_text = "<html><body><ul>{}</ul></body></html>"
        text = ""

        for entry in rows:
            thumbnail = entry.thumbnail
            title = entry.title
            link = entry.link
            description = entry.description
            date_published = entry.date_published
            source = entry.source
            #source_title = entry.source

            text += f'<a href="{link}"><div><img style="width:400px;height=300px" src="{thumbnail}" /></div><div>{title}</div></a><div>{source}</div><div><pre>{description}</pre></div>'

        complete_text = complete_text.format(text)

        with open(self.file_name, "w") as fh:
            fh.write(complete_text)


class OutputWriter(object):

    def __init__(self, conn):
        self.conn = conn

    def write(self):
        rows = self.conn.select_all()
        for entry in rows:
            thumbnail = entry.thumbnail
            title = entry.title
            link = entry.link
            description = entry.description
            date_published = entry.date_published
            source_title = entry.source_title

            print("{} {} {} / {}".format(entry.date_published, entry.link, entry.title, entry.source_title))


class Parser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument(
            "--timeout", default=10, type=int, help="Timeout expressed in seconds"
        )
        self.parser.add_argument("--port", type=int, help="Port")

        self.parser.add_argument("-o", "--output-file", help="Response binary file")
        self.parser.add_argument("-u", "--fetch", action="store_true", help="Fetch files")

        self.args = self.parser.parse_args()


def fetch(conn):
    print("Count:{}".format(conn.count(conn.entries)))

    for source in sources:
        if not conn.is_source(source):
            conn.add_source(source)

        print("Reading {}".format(source))
        source_entries = read_source(source)

        for entry in source_entries:
            if not conn.is_entry(entry):
                conn.add_entry(entry)

        print("Count:{}".format(conn.count(conn.entries)))

    conn.commit()


def do_main(parser):
    WebConfig.use_print_logging()

    # scraping server is not running, we do not use port
    HttpPageHandler.crawling_server_port = 0
    # when python requests cannot handle a scenario, we run crawlee
    HttpPageHandler.crawling_headless_script = "poetry run python crawleebeautifulsoup.py"
    HttpPageHandler.crawling_full_script = "poetry run python crawleebeautifulsoup.py"

    db = SqlModel(db_file="test.db")
    db.remove_older_than_days(7)

    if parser.args.fetch:
        fetch(db)
    elif parser.args.output_file:
        w = HtmlWriter(parser.args.output_file, db)
        w.write()
    else:
        w = OutputWriter(db)
        w.write()

    db.close()


def main():
    p = Parser()
    p.parse()

    do_main(p)


main()
