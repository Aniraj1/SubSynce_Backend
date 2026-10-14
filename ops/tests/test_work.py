from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from ops.tests.helpers import login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


class WorkCompletionTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.priya = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)
        self.job = make_schedule(self.site, self.admin)

    def test_clock_in_and_out_urls_are_gone(self):
        for name in ("clock_in", "clock_out", "portal_check_in", "portal_check_out"):
            with self.assertRaises(NoReverseMatch):
                reverse(f"ops:{name}", args=[self.job.id] if name.startswith("clock") else [])

    def test_contractor_cannot_open_other_contractors_record(self):
        work = CompleteWork.objects.create(schedule=self.job, completed_by=self.alex, status="IN_PROGRESS")
        login(self.client, self.priya)
        self.assertEqual(self.client.get(reverse("ops:work_detail", args=[work.id])).status_code, 404)

    def test_staff_completion_log_and_filters(self):
        CompleteWork.objects.create(schedule=self.job, completed_by=self.alex, status="COMPLETED")
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:completions"))
        self.assertContains(resp, self.site.name)
        resp = self.client.get(reverse("ops:completions"), {"status": "IN_PROGRESS"})
        self.assertNotContains(resp, self.site.name)

    def test_contractor_cannot_see_completion_log(self):
        login(self.client, self.alex)
        self.assertEqual(self.client.get(reverse("ops:completions")).status_code, 403)

    def test_my_jobs_lists_todays_job_without_clock_in(self):
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:my_jobs"))
        self.assertContains(resp, self.site.name)
        self.assertNotContains(resp, "Clock In")
        self.assertNotContains(resp, "Clock Out")
