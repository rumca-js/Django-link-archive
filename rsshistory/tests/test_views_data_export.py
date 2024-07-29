from django.urls import reverse
from django.contrib.auth.models import User
from datetime import time

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
    DomainsController,
    BackgroundJobController,
)
from ..dateutils import DateUtils
from ..models import DataExport

from .fakeinternet import FakeInternetTestCase


class DataExportTests(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser", password="testpassword", is_staff=True
        )

    def test_add_form__init(self):
        DataExport.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export-add".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

    def test_add_form__post_data(self):
        DataExport.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export-add".format(LinkDatabase.name))

        form_data = {
            "enabled": True,
            "export_type": "export-type-git",
            "export_data": "export-dtype-daily-data",
            "local_path": "",
            "remote_path": "",
            "user": "",
            "password": "",
            "db_user": "",
            "export_time": time(0, 0),
        }

        # call user action
        response = self.client.post(url, data=form_data)
        # print(response.text.decode())

        self.assertEqual(response.status_code, 302)

        exports = DataExport.objects.all()
        self.assertEqual(exports.count(), 1)

    def test_edit(self):
        data_export = DataExport.objects.create(
            enabled=True,
            export_type="export-type-git",
            export_data="export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:data-export-edit".format(LinkDatabase.name), args=[data_export.id]
        )

        form_data = {
            "enabled": False,
            "export_type": "export-type-git",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200)

    def test_remove(self):
        data_export = DataExport.objects.create(
            enabled=True,
            export_type="export-type-git",
            export_data="export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:data-export-remove".format(LinkDatabase.name), args=[data_export.id]
        )

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)

        self.assertEqual(DataExport.objects.all().count(), 0)

    def test_list(self):
        data_export = DataExport.objects.create(
            enabled=True,
            export_type="export-type-git",
            export_data="export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-exports".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        data_export = DataExport.objects.create(
            enabled=True,
            export_type="export-type-git",
            export_data="export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export".format(LinkDatabase.name), args=[data_export.id])

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_run__true(self):
        BackgroundJobController.objects.all().delete()

        data_export = DataExport.objects.create(
            enabled=True,
            export_type="export-type-git",
            export_data="export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:data-export-job-add".format(LinkDatabase.name), args=[data_export.id]
        )

        form_data = {
            "enabled": False,
            "export_type": "export-type-git",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 302)

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 1)

    def test_run__false(self):
        BackgroundJobController.objects.all().delete()

        data_export = DataExport.objects.create(
            enabled=False,
            export_type="export-type-git",
            export_data="export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse(
            "{}:data-export-job-add".format(LinkDatabase.name), args=[data_export.id]
        )

        form_data = {
            "enabled": False,
            "export_type": "export-type-git",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200)

        jobs = BackgroundJobController.objects.all()
        self.assertEqual(jobs.count(), 0)
