from django.urls import reverse
from django.contrib.auth.models import User

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

    def test_data_export_add_form(self):
        DataExport.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export-add".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        # redirect to view the link again
        self.assertEqual(response.status_code, 200)

    def test_data_export_add_form(self):
        DataExport.objects.all().delete()

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export-add".format(LinkDatabase.name), args=[])

        form_data = {
            "enabled" : "False",
            "rule_name": "test_rule_edited",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200)

    def test_data_export_edit(self):
        data_export = DataExport.objects.create(
                enabled=True,
                export_type = "export-type-git",
                export_data = "export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export-edit".format(LinkDatabase.name), args=[data_export.id])

        form_data = {
            "enabled" : False,
            "export_type": "export-type-git",
        }

        # call user action
        response = self.client.post(url, data=form_data)

        self.assertEqual(response.status_code, 200)

    def test_data_export_remove(self):
        data_export = DataExport.objects.create(
                enabled=True,
                export_type = "export-type-git",
                export_data = "export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export-remove".format(LinkDatabase.name), args=[data_export.id])

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(DataExport.objects.all().count(), 0)

    def test_data_export_list(self):
        data_export = DataExport.objects.create(
                enabled=True,
                export_type = "export-type-git",
                export_data = "export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-exports".format(LinkDatabase.name), args=[])

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_data_export_detail(self):
        data_export = DataExport.objects.create(
                enabled=True,
                export_type = "export-type-git",
                export_data = "export-dtype-daily-data",
        )

        self.client.login(username="testuser", password="testpassword")

        url = reverse("{}:data-export".format(LinkDatabase.name), args=[data_export.id])

        # call user action
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
