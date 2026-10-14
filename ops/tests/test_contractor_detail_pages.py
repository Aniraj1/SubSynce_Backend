from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ops.tests.helpers import login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


class ContractorDetailPagesTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR", username="alex")
        self.site = make_site(contractor=self.alex, name="Shield Station", price="999.00")
        self.site.cleaning_instructions = "Mop the lobby last."
        self.site.save()
        today = timezone.localdate()
        self.job = make_schedule(self.site, self.admin, day=today + timedelta(days=1))
        self.job.notes = "Use the side door."
        self.job.save()
        login(self.client, self.alex)

    def test_lists_link_to_detail_pages(self):
        self.assertContains(self.client.get(reverse("ops:my_sites")), reverse("ops:my_site_detail", args=[self.site.pk]))
        self.assertContains(self.client.get(reverse("ops:my_jobs")), reverse("ops:my_job_detail", args=[self.job.pk]))
        self.assertContains(self.client.get(reverse("ops:dashboard")), reverse("ops:my_job_detail", args=[self.job.pk]))

    def test_site_page_shows_details_upcoming_and_hides_price(self):
        resp = self.client.get(reverse("ops:my_site_detail", args=[self.site.pk]))
        for text in ("Shield Station", self.site.address, "Mop the lobby last.", "Weekly",
                     self.site.client_id.first_name, reverse("ops:my_job_detail", args=[self.job.pk])):
            self.assertContains(resp, text)
        self.assertNotContains(resp, "999")

    def test_job_page_shows_details_and_work_record(self):
        url = reverse("ops:my_job_detail", args=[self.job.pk])
        resp = self.client.get(url)
        for text in ("Shield Station", "Use the side door.", "Mop the lobby last.", "No work recorded"):
            self.assertContains(resp, text)
        self.assertNotContains(resp, "999")
        work = CompleteWork.objects.create(schedule=self.job, completed_by=self.alex, check_in_time=timezone.now(),
                                           check_out_time=timezone.now(), status="COMPLETED", completion_notes="All clean.")
        resp = self.client.get(url)
        self.assertContains(resp, "All clean.")
        self.assertContains(resp, reverse("ops:work_detail", args=[work.pk]))

    def test_other_contractors_sites_and_jobs_are_404(self):
        bob = make_user("CONTRACTOR", username="bob")
        other_site = make_site(contractor=bob)
        other_job = make_schedule(other_site, self.admin)
        self.assertEqual(self.client.get(reverse("ops:my_site_detail", args=[other_site.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("ops:my_job_detail", args=[other_job.pk])).status_code, 404)

    def test_staff_cannot_use_contractor_pages(self):
        self.client.logout()
        login(self.client, self.admin)
        self.assertNotEqual(self.client.get(reverse("ops:my_site_detail", args=[self.site.pk])).status_code, 200)
