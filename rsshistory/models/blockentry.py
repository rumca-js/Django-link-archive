"""
Defined by automated hosts files, ad block extensions
"""

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.templatetags.static import static
from django.conf import settings

from ..apps import LinkDatabase


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

            wh = self.contents.find("\n")

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

    class Meta:
        ordering = ["-processed", "url"]

    def initialize():
        BlockEntryList.read_lists_group(
            "https://v.firebog.net/hosts/lists.php?type=tick"
        )

    def update_all():
        from ..controllers import BackgroundJobController

        # this creates new lists
        BlockEntryList.read_lists_group(
            "https://v.firebog.net/hosts/lists.php?type=tick"
        )

        # update existing
        for item in BlockEntryList.objects.all():
            item.update()

    def reset():
        BlockEntry.objects.all().delete()
        BlockEntryList.objects.all().delete()
        BlockEntryList.initialize()

    def read_lists_group(lists_group):
        from ..pluginurl import UrlHandler

        url = UrlHandler(lists_group)
        contents = url.get_contents()
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
        from ..pluginurl import UrlHandler

        handler = UrlHandler(self.url)
        contents = handler.get_contents()
        if contents:
            reader = BlockListReader(contents)
            for domain in reader.read():
                blocked = BlockEntry.objects.filter(url=domain)
                if not blocked.exists():
                    BlockEntry.objects.create(url=domain, block_list=self)

        self.processed = True
        self.save()

    def update(self):
        from ..controllers import BackgroundJobController

        BackgroundJobController.create_single_job(
            BackgroundJobController.JOB_INITIALIZE_BLOCK_LIST, self.url
        )


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

    def is_blocked(domain_only_url):
        return BlockEntry.objects.filter(url=domain_only_url).exists()
