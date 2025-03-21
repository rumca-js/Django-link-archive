from django.urls import reverse
from django.contrib.auth.models import User

from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..controllers import (
    SourceDataController,
    LinkDataController,
    DomainsController,
    BackgroundJobController,
)
from ..models import KeyWords

from .fakeinternet import FakeInternetTestCase, MockRequestCounter


class BackgroundJobsViewsTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
            is_staff=True,
        )
        self.client.login(username="testuser", password="testpassword")

    def test_backgroundjobs(self):
        url = reverse("{}:backgroundjobs".format(LinkDatabase.name))

        # call tested function
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_backgroundjob_add(self):
        BackgroundJobController.objects.all().delete()

        url = reverse("{}:backgroundjob-add".format(LinkDatabase.name))

        background_add_data = {
            "job": BackgroundJobController.JOB_CLEANUP,
            "task": "",
            "subject": "",
            "args": "",
        }

        # call tested function
        response = self.client.post(url, data=background_add_data)

        # redirect to see all jobs
        self.assertEqual(response.status_code, 302)

        jobs = BackgroundJobController.objects.all()

        self.assertEqual(jobs.count(), 1)
        # priority is not default, null
        self.assertTrue(jobs[0].priority > 0)

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

        url = reverse(
            "{}:backgroundjob-prio-up".format(LinkDatabase.name), args=[bj.id]
        )
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

        url = reverse(
            "{}:backgroundjob-prio-down".format(LinkDatabase.name), args=[bj.id]
        )
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

        url = reverse(
            "{}:backgroundjob-disable".format(LinkDatabase.name), args=[bj.id]
        )
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

    def test_get_backgroundjobs__no_args(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
            enabled=False,
        )

        url = reverse("{}:get-backgroundjobs".format(LinkDatabase.name))
        # call tested function
        response = self.client.get(url)

        # redirect to see all jobs
        self.assertEqual(response.status_code, 200)

    def test_get_backgroundjobs__job(self):
        bj = BackgroundJobController.objects.create(
            job=BackgroundJobController.JOB_LINK_UPDATE_DATA,
            task=None,
            subject="https://youtube.com?v=1234",
            args="",
            enabled=False,
        )

        url = reverse("{}:get-backgroundjobs".format(LinkDatabase.name))
        url = url + "?job=" + BackgroundJobController.JOB_LINK_UPDATE_DATA

        # call tested function
        response = self.client.get(url)

        # redirect to see all jobs
        self.assertEqual(response.status_code, 200)
