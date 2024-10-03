from datetime import timedelta
from django.contrib.auth.models import User

from ..models import (
        BlockEntry, BlockEntryList, BlockListReader
)
from ..controllers import BackgroundJobController
from ..configuration import Configuration

from .fakeinternet import FakeInternetTestCase, DjangoRequestObject


class BlockListReaderTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

    def test_read__domain_list(self):
        contents = """
# AdguardDNS, parsed and mirrored by https://firebog.net
# Updated 02OCT24 from https://filters.adtidy.org/extension/chromium/filters/15.txt

# This is sourced from an "adblock" style list which is flat-out NOT designed to work with DNS sinkholes
# There WILL be mistakes with how this is parsed, due to how domain names are extracted and exceptions handled
# Please bring any parsing issues up at https://github.com/WaLLy3K/wally3k.github.io/issues prior to raising a request upstream

# If your issue IS STILL PRESENT when using uBlock/ABP/etc, you should request a correction at https://github.com/AdguardTeam/AdGuardSDNSFilter/issues

0024ad98dd.com
002777.xyz
003store.com
00701059.xyz
00771944.xyz
00857731.xyz
0088shop.com
009855.com
00d3ed994e.com
"""
        reader = BlockListReader(contents)

        items = list(reader.read())
        self.assertEqual(len(items), 9)

    def test_read__hosts_file(self):
        contents = """
# AdAway default blocklist
# Blocking mobile ad providers and some analytics providers
#
# Project home page:
# https://github.com/AdAway/adaway.github.io/
#
# Fetch the latest version of this file:
# https://raw.githubusercontent.com/AdAway/adaway.github.io/master/hosts.txt
#
# License:
# CC Attribution 3.0 (http://creativecommons.org/licenses/by/3.0/)
#
# Contributions by:
# Kicelo, Dominik Schuermann.
# Further changes and contributors maintained in the commit history at
# https://github.com/AdAway/adaway.github.io/commits/master
#
# Contribute:
# Create an issue at https://github.com/AdAway/adaway.github.io/issues
#

127.0.0.1  localhost
::1  localhost

# [163.com]
127.0.0.1 analytics.163.com
127.0.0.1 crash.163.com
127.0.0.1 iad.g.163.com
"""
        reader = BlockListReader(contents)

        items = list(reader.read())
        self.assertEqual(len(items), 4)


class BlockEntryListTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()
        self.setup_configuration()

    def test_initialize(self):

        # call tested function
        BlockEntryList.initialize()

        self.assertEqual(BlockEntryList.objects.all().count(), 2)
        self.assertEqual(BackgroundJobController.objects.all().count(), 2)

    def test_reset(self):

        # call tested function
        BlockEntryList.reset()

        self.assertEqual(BlockEntryList.objects.all().count(), 2)
        self.assertEqual(BackgroundJobController.objects.all().count(), 2)

    def test_update_block_entries(self):
        test_list = BlockEntryList.objects.create(url = "https://v.firebog.net/hosts/static/w3kbl.txt")

        # call tested function
        BlockEntryList.update_block_entries(test_list)

        self.assertEqual(BlockEntry.objects.all().count(), 3)
