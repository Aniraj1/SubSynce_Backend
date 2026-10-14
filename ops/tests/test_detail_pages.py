import uuid
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from authuser.model.user import UserDetail
from invoice.model.invoicemanagement import ContractorInvoice
from ops.tests.helpers import login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


class SubcontractorDetailTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR", username="alex")
        UserDetail.objects.create(user=self.alex, first_name="Alex", last_name="Ng", phone="0400111222")
        self.site = make_site(contractor=self.alex, name="Shield Station")
        today = timezone.localdate()
        self.upcoming = make_schedule(self.site, self.admin, day=today + timedelta(days=1))
        done = make_schedule(self.site, self.admin, day=today - timedelta(days=1), status="COMPLETED")
        CompleteWork.objects.create(schedule=done, completed_by=self.alex, check_in_time=timezone.now(),
                                    check_out_time=timezone.now(), status="COMPLETED")
        ContractorInvoice.objects.create(invoice_number="INV-1", site=self.site, invoice_date=today,
                                         service_period_start=today, service_period_end=today,
                                         amount=500, created_by=self.alex, status="APPROVED")

    def test_list_links_name_and_has_no_view_button(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:subcontractors"))
        self.assertContains(resp, reverse("ops:subcontractor_detail", args=[self.alex.pk]))
        self.assertNotContains(resp, "openViewModal")

    def test_detail_shows_profile_sites_upcoming_work_and_earnings(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:subcontractor_detail", args=[self.alex.pk]))
        for text in ("Alex Ng", "@alex", "0400111222", "Shield Station", "$500.00",
                     reverse("ops:site_detail", args=[self.site.pk]),
                     reverse("ops:schedule_detail", args=[self.upcoming.pk])):
            self.assertContains(resp, text)
        self.assertEqual(resp.context["completed_count"], 1)

    def test_detail_staff_only_and_404_for_non_contractor(self):
        login(self.client, self.alex)
        self.assertRedirects(self.client.get(reverse("ops:subcontractor_detail", args=[self.alex.pk])),
                             reverse("ops:dashboard"), fetch_redirect_response=False)
        self.client.logout()
        login(self.client, self.admin)
        self.assertEqual(self.client.get(reverse("ops:subcontractor_detail", args=[self.admin.pk])).status_code, 404)


class ScheduleDetailTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR", username="alex")
        self.site = make_site(contractor=self.alex, name="Shield Station")
        self.schedule = make_schedule(self.site, self.admin, day=timezone.localdate())
        self.schedule.notes = "Bring ladder."
        self.schedule.save()

    def test_list_links_to_detail(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:schedules"))
        self.assertContains(resp, reverse("ops:schedule_detail", args=[self.schedule.pk]))

    def test_detail_without_and_with_work_record(self):
        login(self.client, self.admin)
        url = reverse("ops:schedule_detail", args=[self.schedule.pk])
        resp = self.client.get(url)
        for text in ("Shield Station", "Bring ladder.", self.site.address, "No work recorded",
                     reverse("ops:subcontractor_detail", args=[self.alex.pk]),
                     reverse("ops:client_detail", args=[self.site.client_id.pk])):
            self.assertContains(resp, text)
        work = CompleteWork.objects.create(schedule=self.schedule, completed_by=self.alex,
                                           check_in_time=timezone.now(), completion_notes="All done.")
        resp = self.client.get(url)
        self.assertContains(resp, "All done.")
        self.assertContains(resp, reverse("ops:completion_detail", args=[work.pk]))

    def test_unknown_schedule_404(self):
        login(self.client, self.admin)
        self.assertEqual(self.client.get(reverse("ops:schedule_detail", args=[uuid.uuid4()])).status_code, 404)


class ContractorDeleteAndNamingTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        login(self.client, self.admin)

    def test_list_and_detail_offer_delete(self):
        bob = make_user("CONTRACTOR", username="bob")
        delete_url = reverse("ops:user_delete", args=[bob.pk])
        self.assertContains(self.client.get(reverse("ops:subcontractors")), delete_url)
        self.assertContains(self.client.get(reverse("ops:subcontractor_detail", args=[bob.pk])), delete_url)

    def test_delete_without_linked_records_removes_and_blocks_login(self):
        from authuser.model.user import User
        bob = make_user("CONTRACTOR", username="bob")
        resp = self.client.post(reverse("ops:user_delete", args=[bob.pk]), {"next": reverse("ops:subcontractors")})
        self.assertRedirects(resp, reverse("ops:subcontractors"), fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=bob.pk, deleted_at__isnull=True).exists())
        self.assertNotContains(self.client.get(reverse("ops:subcontractors")), "@bob")

    def test_delete_refused_while_contractor_has_sites(self):
        from authuser.model.user import User
        alex = make_user("CONTRACTOR", username="alex")
        make_site(contractor=alex)
        resp = self.client.post(reverse("ops:user_delete", args=[alex.pk]), {"next": reverse("ops:subcontractors")}, follow=True)
        self.assertContains(resp, "Can&#x27;t delete alex")
        self.assertTrue(User.objects.filter(pk=alex.pk, deleted_at__isnull=True).exists())

    def test_pages_say_contractor_not_subcontractor(self):
        alex = make_user("CONTRACTOR", username="alex")
        site = make_site(contractor=alex)
        sched = make_schedule(site, self.admin)
        for url in (reverse("ops:subcontractors"), reverse("ops:subcontractor_detail", args=[alex.pk]),
                    reverse("ops:schedules") + "?period=all", reverse("ops:schedule_detail", args=[sched.pk]),
                    reverse("ops:dashboard"), reverse("ops:completions")):
            self.assertNotIn("subcontractor", self.client.get(url).content.decode().lower().replace("ops:subcontractor", ""), url)
        self.client.logout()
        login(self.client, alex)
        self.assertNotContains(self.client.get(reverse("ops:dashboard")), "Subcontractor")

    def test_add_contractor_from_contractors_page(self):
        from authuser.model.user import User
        page = reverse("ops:subcontractors")
        self.assertContains(self.client.get(page), "Add Contractor")
        data = {"first_name": "Nat", "last_name": "R", "username": "natr", "email": "nat@example.com",
                "role": "CONTRACTOR", "password1": "Strong#Pass123", "password2": "Strong#Pass123", "next": page}
        resp = self.client.post(reverse("ops:user_create"), data)
        self.assertRedirects(resp, page, fetch_redirect_response=False)
        self.assertEqual(User.objects.get(username="natr").role, "CONTRACTOR")
        self.assertContains(self.client.get(page), "@natr")

    def test_failed_add_reopens_form_with_errors_on_contractors_page(self):
        page = reverse("ops:subcontractors")
        data = {"first_name": "Nat", "username": "natr", "email": "nat@example.com", "role": "CONTRACTOR",
                "password1": "Strong#Pass123", "password2": "Different#1", "next": page}
        self.client.post(reverse("ops:user_create"), data)
        resp = self.client.get(page)
        self.assertContains(resp, "Passwords do not match.")
        self.assertContains(resp, '"username": "natr"')


class ContractorCannotManageContractorsTests(TestCase):
    def test_contractor_is_blocked_from_every_contractor_admin_action(self):
        from authuser.model.user import User
        other = make_user("CONTRACTOR", username="other")
        me = make_user("CONTRACTOR", username="me")
        login(self.client, me)
        dashboard = reverse("ops:dashboard")
        for url in (reverse("ops:subcontractors"), reverse("ops:subcontractor_detail", args=[other.pk])):
            self.assertRedirects(self.client.get(url), dashboard, fetch_redirect_response=False)
        self.client.post(reverse("ops:user_delete", args=[other.pk]))
        self.client.post(reverse("ops:subcontractor_update", args=[other.pk]), {"first_name": "X", "username": "hacked", "email": "x@example.com"})
        self.client.post(reverse("ops:user_create"), {"first_name": "N", "username": "newbie", "email": "n@example.com", "role": "CONTRACTOR",
                                                      "password1": "Strong#Pass123", "password2": "Strong#Pass123"})
        other.refresh_from_db()
        self.assertIsNone(other.deleted_at)
        self.assertEqual(other.username, "other")
        self.assertFalse(User.objects.filter(username="newbie").exists())
        # Nothing on the contractor's own pages links to these admin actions.
        for url in (dashboard, reverse("ops:invoices")):
            html = self.client.get(url).content.decode()
            for name in ("ops:subcontractors", "ops:user_create"):
                self.assertNotIn(reverse(name), html)

    def test_contractor_gets_no_admin_page(self):
        login(self.client, make_user("CONTRACTOR"))
        for name in ("clients", "client_create", "sites", "schedules", "users", "subcontractors", "calendar",
                     "completions", "client_invoices", "client_invoice_create", "profitability", "company_settings"):
            resp = self.client.get(reverse(f"ops:{name}"))
            self.assertIn(resp.status_code, (302, 403), name)
            if resp.status_code == 302:
                self.assertEqual(resp.url, reverse("ops:dashboard"), name)
