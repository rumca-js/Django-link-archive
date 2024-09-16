from pathlib import Path
import shutil
import json

from utils.dateutils import DateUtils

from ..models import ConfigurationEntry, DataExport
from ..controllers import SourceDataController, LinkDataController, DomainsController
from ..configuration import Configuration
from ..datawriter import DataWriter, DataWriterConfiguration

from .fakeinternet import FakeInternetTestCase


class DataWriterTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.test_export_path = Path("./test_data/exports")
        self.remove_all_files()

        source_youtube = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent2",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            bookmarked=True,
            date_published=DateUtils.from_string("2024-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )

        DomainsController.add("https://youtube.com?v=nonbookmarked")

        self.export_daily = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        self.export_year = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=False,
            export_sources=True,
        )

        self.export_notime = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

    def tearDown(self):
        self.remove_all_files()

    def remove_all_files(self):
        if self.test_export_path.exists():
            shutil.rmtree(self.test_export_path.as_posix())
            shutil.rmtree(self.test_export_path.parent.as_posix())

    def test_domain_json(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        dw_conf = DataWriterConfiguration(
            conf, self.export_daily, Path("./data/test/daily_data")
        )
        writer = DataWriter.get(dw_conf)

        # call tested function
        json_text = writer.get_domains_json()

        json_obj = json.loads(json_text)

        self.assertEqual(len(json_obj), 1)

    def test_write__year__json(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = True
        self.export_year.format_md = False
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_year, Path("./data/test/year")
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 2)

        json_file = Path("./data") / "test" / "year" / "2023" / "bookmarks_entries.json"
        self.assertEqual(json_file.exists(), True)

        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 1)

        json_file = Path("./data") / "test" / "year" / "sources.json"
        self.assertEqual(json_file.exists(), True)

        json_file = Path("./data") / "test" / "year" / "2024" / "bookmarks_entries.json"
        self.assertEqual(json_file.exists(), True)

    def test_write__notime__json(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = True
        self.export_year.format_md = False
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_notime, Path("./data/test/notime")
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 2)

        json_file = Path("./data") / "test" / "notime" / "permanent" / "00000" / "permanent_entries.json"
        self.assertEqual(json_file.exists(), True)
        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 1)

        json_file = Path("./data") / "test" / "notime" / "sources.json"
        self.assertEqual(json_file.exists(), True)

    def test_write__daily_data__json(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = True
        self.export_year.format_md = False
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_daily, Path("./data/test/daily_data"), "2023-03-03"
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        json_file = (
            Path("./data")
            / "test"
            / "daily_data"
            / "2023"
            / "03"
            / "2023-03-03"
            / "https...youtube.com_entries.json"
        )
        json_obj = json.loads(json_file.read_text())

        self.assertEqual(len(json_obj), 3)

        json_file = Path("./data") / "test" / "daily_data" / "sources.json"
        self.assertEqual(json_file.exists(), True)

        # 2024 should not be exported
        json_file = Path("./data") / "test" / "daily_data" / "2024" / "03"
        self.assertEqual(json_file.exists(), False)

    def test_write__notime__many_sources(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        for source_idx in range(2000):
            SourceDataController.objects.create(
                url="https://linkedin.com/{}".format(source_idx),
                title="LinkedIn{}".format(source_idx),
                category="No",
                subcategory="No",
                export_to_cms=True,
            )

        conf = Configuration.get_object()

        self.export_year.format_json = True
        self.export_year.format_md = False
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_notime, Path("./data/test/notime")
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 2)

        json_file = Path("./data") / "test" / "notime" / "permanent" / "00000" / "permanent_entries.json"
        self.assertEqual(json_file.exists(), True)
        json_obj = json.loads(json_file.read_text())
        self.assertEqual(len(json_obj), 1)

        json_dir = Path("./data") / "test" / "notime" / "sources"
        self.assertEqual(json_dir.exists(), True)

        json_file = (
            Path("./data") / "test" / "notime" / "sources" / "00000" / "sources.json"
        )
        self.assertEqual(json_file.exists(), True)

    def test_write__year__md(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = False
        self.export_year.format_md = True
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_year, Path("./data/test/year")
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 2)

        md_file = Path("./data") / "test" / "year" / "2023" / "bookmarks_entries.md"
        self.assertEqual(md_file.exists(), True)

        md_file = Path("./data") / "test" / "year" / "2024" / "bookmarks_entries.md"
        self.assertEqual(md_file.exists(), True)

    def test_write__notime__md(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = False
        self.export_year.format_md = True
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_notime, Path("./data/test/notime")
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 2)

        md_file = Path("./data") / "test" / "notime" / "permanent" / "00000" / "permanent_entries.md"
        self.assertEqual(md_file.exists(), True)

    def test_write__daily_data__md(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = False
        self.export_year.format_md = True
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_daily, Path("./data/test/daily_data"), "2023-03-03"
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        md_file = (
            Path("./data")
            / "test"
            / "daily_data"
            / "2023"
            / "03"
            / "2023-03-03"
            / "https...youtube.com_entries.md"
        )

        self.assertTrue(md_file.exists())

        # 2024 should not be exported
        json_file = Path("./data") / "test" / "daily_data" / "2024" / "03"
        self.assertEqual(json_file.exists(), False)

    def test_write__year__html(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = False
        self.export_year.format_md = False
        self.export_year.format_rss = False
        self.export_year.format_html = True
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_year, Path("./data/test/year")
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 2)

        html_directory = Path("./data") / "test" / "year" / "html"
        self.assertEqual(html_directory.exists(), True)

    def test_write__notime__md(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = False
        self.export_year.format_md = True
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_notime, Path("./data/test/notime")
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        links = LinkDataController.objects.filter(bookmarked=True)
        self.assertEqual(links.count(), 2)

        html_directory = Path("./data") / "test" / "notime" / "html"
        self.assertEqual(html_directory.exists(), True)

    def test_write__daily_data__md(self):
        entry = ConfigurationEntry.get()
        entry.data_export_path = self.test_export_path
        entry.save()

        conf = Configuration.get_object()

        self.export_year.format_json = False
        self.export_year.format_md = True
        self.export_year.format_rss = False
        self.export_year.format_html = False
        self.export_year.save()

        dw_conf = DataWriterConfiguration(
            conf, self.export_daily, Path("./data/test/daily_data"), "2023-03-03"
        )
        writer = DataWriter.get(dw_conf)
        # call tested function
        writer.write()

        html_dir = (
            Path("./data")
            / "test"
            / "daily_data"
            / "2023"
            / "03"
            / "html"
        )

        self.assertTrue(html_dir.exists())
