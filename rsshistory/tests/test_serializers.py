from pathlib import Path
from django.contrib.auth.models import User

from utils.dateutils import DateUtils
from utils.services import ReadingList

from ..serializers import MarginaliaCrawlerOutput, EntryYearDataMainExporter
from ..models import UserBookmarks, DataExport
from ..controllers import LinkDataController
from ..configuration import Configuration
from ..datawriter import DataWriterConfiguration

from .fakeinternet import FakeInternetTestCase


default_marginalia_data = """www.serious-coin.com 2023-12-27T05:10:48.915921325 5a/28/5a284524-www.seriousXcoin.com.parquet 45
digitalarchives.usi.edu 2023-12-27T17:54:38.997419605 10/0c/100cfdee-digitalarchives.usi.edu.parquet 4
blacksheephouse.co.uk 2023-12-27T08:13:37.640463830 a6/8b/a68b20ce-blacksheephouse.co.uk.parquet 9
"""


class MarginaliaCrawlerOutputTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_data(self):
        p = MarginaliaCrawlerOutput(default_marginalia_data)
        links = p.get_links()

        self.assertEqual(len(links), 3)
        self.assertEqual(links[0], "www.serious-coin.com")


default_reading_list_data = """url,title,description,image,date,hnurl
https://www.thedrive.com/news/41493/teslas-16000-quote-for-a-700-fix-is-why-right-to-repair-matters,"Tesla’s $16,000 Quote for a $700 Fix Is Why Right to Repair Matters",This is what people are fighting for.,,2021-07-13T22:14:18.423350404Z,https://news.ycombinator.com/item?id=27814621
https://hakibenita.com/django-nested-transaction,One Database Transaction Too Many | Haki Benita,How I told hundreds of users they got paid when they didn't!,,2021-07-13T22:24:56.413065045Z,https://news.ycombinator.com/item?id=27804716
https://news.ycombinator.com/item?id=27814080,This Website is hosted on an Casio fx-9750GII Calculator | Hacker News,,,2021-07-13T22:25:42.431079257Z,
https://www.theverge.com/2021/7/12/22573850/elon-musk-richard-branson-spaceplane-virgin-galactic,Elon Musk has a ticket to ride on Richard Branson’s spaceplane - The Verge,Billionaire Musk will someday fly billionaire Branson’s plane.,,2021-07-13T22:33:11.442269385Z,
"""


class ReadingListTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_data(self):
        p = ReadingList(default_reading_list_data)
        links = p.get_links()

        self.assertEqual(len(links), 4)
        self.assertEqual(
            links[0],
            "https://www.thedrive.com/news/41493/teslas-16000-quote-for-a-700-fix-is-why-right-to-repair-matters",
        )
