"""
This script is not required, SeleniumUndetected can be called directly from a project.
 - we just show off how it can be done
 - it can be used to compare with other crawling scripts
"""

import json
import time
import argparse
import sys

import webtools


def main():
    webtools.WebConfig.use_print_logging() 

    parser = webtools.ScriptCrawlerParser()
    parser.parse()
    if not parser.is_valid():
        sys.exit(1)
        return

    request = parser.get_request()

    driver = webtools.SeleniumUndetected(request, parser.args.output_file, parser.args.port)

    if parser.args.verbose:
        print("Running request:{} with SeleniumUndetected".format(request))

    if not driver.run():
        sys.exit(1)
        return

    driver.save_response()


main()