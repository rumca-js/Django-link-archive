"""
Defined by automated hosts files, ad block extensions
"""

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.templatetags.static import static
from django.conf import settings

from ..apps import LinkDatabase
from .system import AppLogging


class BlockListReader(object):
    def __init__(self, contents):
        self.contents = contents

    def read(self):
        self.contents = self.contents.replace("\r", "")

        while True:
            wh = self.contents.find("\n")
            if wh == -1:
                return

            line = self.contents[:wh]
            self.contents = self.contents[wh + 1 :]

            line = line.strip()
            if not line:
                continue

            if not self.is_line_valid(line):
                continue

            line = self.process_line(line)
            if line:
                yield line

    def process_line(self, line):
        domain = None

        line = self.strip_comments(line)

        # read various lines

        if line.startswith("||"):
            domain = self.read_custom_line(line)
        elif line.find(" ") >= 0 or line.find("\t") >= 0:
            domain = self.read_host_line(line)
        else:
            domain = self.read_normal_line(line)

        if domain and domain != "":
            return domain

    def is_line_valid(self, line):
        line = line.strip()

        if not line:
            return False
        if line is None:
            return False
        if line == "":
            return False

        # skip comments
        forbidden_starts = [
            "#",
            ":",
            ";",
            "!",
        ]

        found_forbidden = False
        for forbidden_start in forbidden_starts:
            if line.startswith(forbidden_start):
                found_forbidden = True
                break

        if found_forbidden:
            return False

        return True

    def strip_comments(self, line):
        # example 'adsunflower.com #Android Trojan - Malware'
        wh = line.find("#")
        if wh >= 0:
            return line[:wh].strip()

        return line

    def read_custom_line(self, line):
        return line[2:-1]

    def read_host_line(self, line):
        wh = line.find(" ")
        first_part = line[:wh].strip()
        second_part = line[wh + 1 :].strip()

        return second_part

    def read_normal_line(self, line):
        return line


class BlockEntryList(models.Model):
    url = models.CharField(max_length=1000, unique=True)
    processed = models.BooleanField(default=False)

    STARTUP_ENTRY_LIST = "https://v.firebog.net/hosts/lists.php?type=tick"

    class Meta:
        ordering = ["-processed", "url"]

    def __str__(self):
        return "BlockEntryList Id:{} Url:{}".format(self.id, self.url)

    def initialize():
        BlockEntryList.update_all()

    def update_all():
        from ..pluginurl import UrlHandler

        # this creates new lists
        BlockEntryList.read_lists_group(BlockEntryList.STARTUP_ENTRY_LIST)

        for alist in BlockEntryList.objects.all():
            if not UrlHandler.ping(alist.url):
                alist.delete()
            else:
                alist.update()

    def update(self):
        from ..pluginurl import UrlHandler
        from ..controllers import BackgroundJobController

        if not UrlHandler.ping(self.url):
            return False

        self.processed = False
        self.save()

        BackgroundJobController.create_single_job(
            BackgroundJobController.JOB_INITIALIZE_BLOCK_LIST, self.url
        )
        return True

    def reset():
        BlockEntry.objects.all().delete()
        BlockEntryList.objects.all().delete()
        BlockEntryList.initialize()

    def read_lists_group(lists_group):
        from ..pluginurl import UrlHandler

        url = UrlHandler(lists_group)
        contents = url.get_text()
        if contents:
            lines = contents.split("\n")
            BlockEntryList.add_lists(lines)

    def add_lists(lists):
        for item in lists:
            item = item.replace("\r", "")
            if item.strip() != "":
                wh = item.find("http")
                item = item[wh:]

                BlockEntryList.add_list(item)

    def add_list(thelist):
        item = thelist.replace("\r", "")
        blocked_lists = BlockEntryList.objects.filter(url=item)
        if not blocked_lists.exists():
            block_list = BlockEntryList.objects.create(url=item)
            block_list.update()

    def update_implementation(self):
        """
        @note Called from initialize block list
        """
        from ..pluginurl import UrlHandler

        handler = UrlHandler(self.url)
        contents = handler.get_text()
        if contents:
            reader = BlockListReader(contents)
            AppLogging.debug("Reading block list {}".format(self.url))

            for domain in reader.read():
                blocked = BlockEntry.objects.filter(url=domain)
                if not blocked.exists():
                    AppLogging.debug("Added {}".format(domain))
                    BlockEntry.objects.create(url=domain, block_list=self)

        self.processed = True
        self.save()


class BlockEntry(models.Model):
    url = models.CharField(max_length=1000, unique=True)

    block_list = models.ForeignKey(
        BlockEntryList,
        on_delete=models.CASCADE,
        related_name="entries",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["url"]

    def __str__(self):
        return "BlockEntry Url:{} {}".format(self.url, self.block_list)

    def is_blocked(domain_only_url):
        return BlockEntry.objects.filter(url=domain_only_url).exists()

    def get_entry(domain_only_url):
        blocks = BlockEntry.objects.filter(url=domain_only_url)
        if blocks.exists():
            return blocks[0]
