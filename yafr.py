"""
This is example script about how to use this project as a simple RSS reader
"""
from webtools import (
   WebConfig,
   HttpPageHandler,
   FeedClientParser,
   FeedClient,
   ScrapingClient,
)
from sqlalchemy import (
    create_engine,
)
from utils.logger import Logger

def main():
    WebConfig.init()
    # we do not want to be swamped with web requests
    #WebConfig.use_print_logging()
    Logger.use_print_logging()

    parser = FeedClientParser()
    parser.parse()

    engine = create_engine("sqlite:///feedclient.db")

    p = FeedClient(day_limit=7, engine=engine, parser=parser)

    if p.parser.args.verbose:
        WebConfig.use_print_logging()

    # if scraping server is running, use it
    c = ScrapingClient()
    c.set_scraping_script("poetry run python crawleebeautifulsoup.py")
    if c.connect():
        c.close()
        WebConfig.crawling_server_port = c.port
    else:
        WebConfig.crawling_server_port = 0

    # scraping server is not running, we do not use port
    #WebConfig.crawling_full_script = None
    #WebConfig.crawling_headless_script = None

    WebConfig.crawling_full_script = "poetry run python crawleebeautifulsoup.py"
    WebConfig.crawling_headless_script = "poetry run python crawleebeautifulsoup.py"

    p.run()

main()
