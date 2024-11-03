import json
from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import (
    BackgroundJobController,
)

from .fakeinternet import FakeInternetTestCase


class ExportTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

class ImportTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_import_from_files__init(self):
        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:import-from-files".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

    def test_import_from_files__post(self):
        BackgroundJobController.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:import-from-files".format(LinkDatabase.name), args=[])

        # call user action
        import_data = {
            "path": "/test/path/location",
            "username": "rumpel",
            "import_entries": True,
            "import_sources": True,
            "import_title": True,
            "import_description": True,
            "import_tags": True,
            "import_comments": True,
            "import_votes": True,
            "import_bookmarks": True,
        }

        # call user action
        response = self.client.post(url, data=import_data)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 1)

        job = jobs[0]
        self.assertEqual(job.job, BackgroundJobController.JOB_IMPORT_FROM_FILES)

        try:
            data = json.loads(job.subject)
        except ValueError as E:
            self.assertTrue(False)

        self.assertTrue("username" in data)
        self.assertEqual(data["username"], "rumpel")
        self.assertTrue("path" in data)
        self.assertEqual(data["path"], "/test/path/location")
        self.assertTrue("import_entries" in data)
        self.assertEqual(data["import_entries"], True)
