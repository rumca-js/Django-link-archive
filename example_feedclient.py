"""
This is example script about how to use this project as a simple RSS reader
"""
import socket
import json
import traceback

from rsshistory.webtools import (
    PageOptions,
    WebConfig,
    WebLogger,
    PrintWebLogger,
    Url,
    HttpPageHandler,
)


sources = [
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCXGgrKt94gR6lmN4aN3mYTg", "austin evans"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCyl5V3-J_Bsy3x-EBCJwepg", "babylon bee"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCmrLCXSDScliR7q8AxxjvXg", "black pidgeon speaks"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC7vVhkEfw4nOGp8TyDk7RcQ", "boston dynamics"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UClozNP-QPyVatzpGKC25s0A", "brad colbow"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCld68syR8Wi-GY_n4CaoJGA", "brodie robertson"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCROQqK3_z79JuTetNP3pIXQ", "captain midnight"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCtinbF-Q-fVthA0qrFQTgXQ", "casey"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCxHAlbZQNFU2LgEtiqd2Maw", "c++ weekly with jason turner"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCLLO-H4NQXNa_DhUv-rqN9g", "cd action"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCPKT_csvP72boVX0XrMtagQ", "cercle"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCwjvvgGX6oby5mZ3gbDe8Ug", "china insights"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCgFP46yVT-GG4o1TgXn-04Q", "china uncensored"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCg6gPGh8HU2U01vaFCAsvmQ", "christ titus tech"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCFQMnBA3CS502aghlcr0_aw", "cofeezilla"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCX_t3BvnQtS5IHzto_y7tbw", "coreteks"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC4QZ_LsYcvcq7qOsOhpAX4A", "coldfusion"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC9Ntx-EF3LzKY1nQ5rTUP2g", "cyriak"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCVls1GmFKf6WlTraIb_IaJg", "distrotube"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCTSRIY3GLFYIpkR2QwyeklA", "drew gooden"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCD4EOyXKjfDUhCI6jlOZZYQ", "eli the computer guy"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCCDGVMGoT8ql8JQLJt715jA", "emzdanowicz"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCDNHPNeWScAC8h8IxtEBtkQ", "eons of battle"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC_0CVCfC_3iuHqmyClu59Uw", "eta prime"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCO7fujFV_MuxTM0TuZrnE6Q", "felix colgrave"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCG_nvdTLdijiAAuPKxtvBjA", "filmento"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCNnKprAG-MWLsk-GsbsC2BA", "flashgitz"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCyNtlmLB73-7gtlBz00XOQQ", "folding ideas"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC2WHjPDvbE6O328n17ZGcfg", "forrest knight"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCRG_N2uO405WO4P3Ruef9NA", "friday checkout"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCHDxYLv8iovIbhrfl16CNyg", "gamelinked"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCNvzD7Z-g64bPXxGzaQaa4g", "gameranx"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCbu2SsF-Or3Rsn3NxqODImw", "gamespot"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCXa_bzvv7Oo1glaW9FldDhQ", "gaming bolt"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCmEbe0XH51CI09gm_9Fcn8Q", "glass reflection"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCkPjHTuNd_ycm__29dXM3Nw", "gf darwin"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCR-DXc1voovS8nhAvccRZhg", "jeff gerling"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCoOjH8D2XAgjzQlneM2W0EQ", "jake tran"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC7v3-2K1N84V67IF-WTRG-Q", "jeremy jahns"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC-2YHgc363EdcusLIBbgxzg", "joe scott"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCVIFCOJwv3emlVmBbPCZrvw", "joel havier"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCmGSJVG3mCRXVOP4yZrU1Dw", "john harris"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC337i8LcUSM4UMbLf820I8Q", "just some guy"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCLRlryMfL8ffxzrtqv0_k_w", "kino check"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCG2kQBVlgG7kOigXZTcKrQw", "kolem sie toczy"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC2_KC8lshtCyiLApy27raYw", "knowledgehusk"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCLr4hMhk_2KE0GUBSBrspGA", "kuba klawiter"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCJKt_QVDyUbqdm3ag_py2eQ", "kuokka77"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCtVGGeUqfVHOK4Q6nAwYO3g", "laterclips"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCXuqSBlHAE6Xw-yeJA0Tunw", "linus tech tips"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCl2mFZoRqjw_ELax4Yisf6w", "louis rossman"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC2eYFnH61tmytImy1mTYvhA", "luke smith"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UClOGLGPOqlAiLmOvXW5lKbw", "mandalore gaming"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCBJycsmduvYEL83R_U4JriQ", "marques brownlee"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCTTZqMWBvLsUYqYwKTdjvkw", "mateusz chrobok"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCjuKQCmKlCtrPL2wl1uIphQ", "more pegasus"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC5T0tXJN5CrMZUEJuz4oovw", "nerdrotic"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCe6nK69Yc1zna7QSJEfA9pw", "niebezpiecznik"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCittVh8imKanO_5KohzDbpg", "paul joseph watson"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCswH8ovgUp5Bdg-0_JTYFNw", "russel brand"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCh9IfI45mmk59eDvSWtuuhQ", "ryan george"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCzKFvBRI6VT3jYJq6a820nA", "ryan long"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCA3-nIYWu4PTWkb6NwhEpzg", "ryan reynolds"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCyseFvMP4mZVlU5iEEbAamA", "salvatore ganacci"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCd6vEDS3SOhWbXZrxbrf_bw", "samtime"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCEq_Dr1GHvnNPQNfgOzhZ8Q", "solid jj"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCD6VugMZKRhSyzWEWA9W2fg", "sssethtzeentach"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCDvZTWvHZPTxJ4K1yTD2a1g", "squidmar miniatures"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UC2CKTY1TXQ4YQ3AHvyCgtbQ", "tabletop miniatures"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCtZO3K2p8mqFwiKWb9k7fXA", "techaltar"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCeeFfhMcJa1kjtfZAGskOCA", "techlinked"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCSJPFQdZwrOutnmSFYtbstA", "the critical drinker"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCjr2bPAyPV7t35MvcgT3W8Q", "the hated one"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCDVb4m_5QHhZElT47E1oODg", "dave cullen show"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCSbdMXOI_3HGiFviLZO6kNA", "thrillseeker"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCQSpnDG3YsFNf5-qHocF-WQ", "thiojoe"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCRlICXvO4XR4HMeEB9JjDlA", "thoughty2"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCxt2r57cLastdmrReiQJkEg", "tom nicolas"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCBa659QWEk1AI4Tg--mrJ2A", "tom scott"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCFLwN7vRu8M057qJF8TsBaA", "up is not down"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCvg_4SPPEZ7y4pk_iB7z6sw", "whimsu"],
       ["https://www.youtube.com/feeds/videos.xml?channel_id=UCxXu9tCU63mF1ntk89XPkzA", "worthkids"],
       # ["https://www.warhammer-community.com/feed", "Warhammer community"],
]


def read_source(source):
    result = []

    source_url = source[0]
    source_title = source[1]

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


def main():
    WebConfig.use_print_logging()

    # scraping server is not running, we do not use port
    HttpPageHandler.crawling_server_port = 0
    # when python requests cannot handle a scenario, we run crawlee
    HttpPageHandler.crawling_headless_script = "poetry run python crawleebeautifulsoup.py"
    HttpPageHandler.crawling_full_script = "poetry run python crawleebeautifulsoup.py"
    
    entries = []
    for source in sources:
        print("Reading {}".format(source))
        source_entries = read_source(source)
        entries.extend(source_entries)
    
    entries = sorted(entries, key = lambda x: x['date_published'], reverse=True)
    
    for entry in entries:
        print("{} {} {} / {}".format(entry["date_published"], entry["link"], entry["title"], entry["source_title"]))


main()
