from datetime import timedelta
from django.contrib.auth.models import User

from ..models import BlockEntry, BlockEntryList, BlockListReader
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

    def test_read__hosts_file__with_comments(self):
        contents = """
# AdAway default blocklist
#
# Contribute:
# Create an issue at https://github.com/AdAway/adaway.github.io/issues
#

127.0.0.1  localhost
::1  localhost

# [163.com]
127.0.0.1 analytics.163.com
127.0.0.1 crash.163.com  # this is a comment
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

        block_lists = BlockEntryList.objects.all()

        self.assertEqual(block_lists.count(), 2)
        self.assertEqual(BackgroundJobController.objects.all().count(), 2)

    def test_reset(self):
        # call tested function
        BlockEntryList.reset()

        self.assertEqual(BlockEntryList.objects.all().count(), 2)
        self.assertEqual(BackgroundJobController.objects.all().count(), 2)

    def test_update__w3kbl(self):
        test_list = BlockEntryList.objects.create(
            url="https://v.firebog.net/hosts/static/w3kbl.txt"
        )

        # call tested function
        test_list.update_implementation()

        self.assertEqual(BlockEntry.objects.all().count(), 3)

        self.assertEqual(test_list.processed, True)

    def test_update__rpi(self):
        test_list = BlockEntryList.objects.create(
            url="https://v.firebog.net/hosts/RPiList-Malware.txt"
        )

        # call tested function
        test_list.update_implementation()

        block_entries = BlockEntry.objects.all()

        for entry in block_entries:
            print(entry.url)

        self.assertEqual(block_entries.count(), 7)

        urls = block_entries.values_list("url", flat=True)
        self.assertTrue(
            "0-00d10140000motieas-990auyn11w0wpnuy4.dcsportal.0-astrologie.net.daraz.com"
            in urls
        )

        self.assertEqual(test_list.processed, True)

    def tearDown(self):
        BlockEntry.objects.all().delete()
