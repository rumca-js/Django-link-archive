from django.urls import reverse
from django.contrib.auth.models import User

from ..apps import LinkDatabase
from ..controllers import SourceDataController, LinkDataController, DomainsController, BackgroundJobController
from ..dateutils import DateUtils
from ..models import KeyWords, DataExport

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class SystemViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_index(self):
        url = reverse("{}:index".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_admin(self):
        url = reverse("{}:admin-page".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_user_config(self):
        url = reverse("{}:user-config".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_configuration(self):
        url = reverse("{}:configuration".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_system_status(self):
        url = reverse("{}:system-status".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_about(self):
        url = reverse("{}:about".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_reset_config(self):
        url = reverse("{}:reset-config".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_system_status(self):
        url = reverse("{}:system-status".format(LinkDatabase.name))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    # Background jobs

    def test_backgroundjobs(self):
        url = reverse("{}:backgroundjobs".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_backgroundjob_remove(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
        )

        url = reverse("{}:backgroundjob-remove".format(LinkDatabase.name), args=[bj.id])
        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_backgroundjob_remove(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
        )

        url = reverse("{}:backgroundjob-remove".format(LinkDatabase.name), args=[bj.id])
        # call tested function
        response = self.client.get(url)

        # redirect to see all jobs
        self.assertEqual(response.status_code, 302)

    def test_backgroundjobs_remove_fail(self):
        url = reverse("{}:backgroundjobs-remove".format(LinkDatabase.name), args=["0"])

        # call tested function
        response = self.client.get(url)

        # redirect to see all jobs
        self.assertEqual(response.status_code, 302)

    def test_backgroundjob_prio_up(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
        )

        original_priority = bj.priority

        url = reverse("{}:backgroundjob-prio-up".format(LinkDatabase.name), args=[bj.id])
        # call tested function
        response = self.client.get(url)

        bj.refresh_from_db()

        # redirect to see all jobs
        self.assertEqual(response.status_code, 302)

        self.assertEqual(bj.priority, original_priority - 1)

    def test_backgroundjob_prio_down(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
        )

        original_priority = bj.priority

        url = reverse("{}:backgroundjob-prio-down".format(LinkDatabase.name), args=[bj.id])
        # call tested function
        response = self.client.get(url)

        bj.refresh_from_db()

        # redirect to see all jobs
        self.assertEqual(response.status_code, 302)

        self.assertEqual(bj.priority, original_priority + 1)

    def test_backgroundjob_disable(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
            enabled=True,
        )

        url = reverse("{}:backgroundjob-disable".format(LinkDatabase.name), args=[bj.id])
        # call tested function
        response = self.client.get(url)

        bj.refresh_from_db()

        # redirect to see all jobs
        self.assertEqual(response.status_code, 302)

        self.assertEqual(bj.enabled, False)

    def test_backgroundjob_enable(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
            enabled=False,
        )

        url = reverse("{}:backgroundjob-enable".format(LinkDatabase.name), args=[bj.id])
        # call tested function
        response = self.client.get(url)

        bj.refresh_from_db()

        # redirect to see all jobs
        self.assertEqual(response.status_code, 302)

        self.assertEqual(bj.enabled, True)
