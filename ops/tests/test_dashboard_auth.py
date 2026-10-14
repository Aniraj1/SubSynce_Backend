from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from ops.tests.helpers import PASSWORD, login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


class LoginTests(TestCase):
    def test_next_param_cannot_redirect_off_site(self):
        user = make_user("ADMINISTRATOR")
        resp = self.client.post("/?next=https://evil.example/", {"username": user.username, "password": PASSWORD})
        self.assertRedirects(resp, reverse("ops:dashboard"))

    def test_next_param_keeps_local_paths(self):
        user = make_user("ADMINISTRATOR")
        resp = self.client.post("/?next=/completions/", {"username": user.username, "password": PASSWORD})
        self.assertRedirects(resp, "/completions/")


class DashboardTests(TestCase):
    def setUp(self):
        self.owner = make_user("OWNER")
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)
        done = make_schedule(self.site, self.admin, day=date.today() - timedelta(days=1))
        CompleteWork.objects.create(schedule=done, completed_by=self.alex, status="COMPLETED")
        make_schedule(self.site, self.admin)
        ClientInvoice.objects.create(
            invoice_number="C-1", site=self.site, client=self.site.client_id, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(),
            amount=Decimal("1800.00"), status="PAID", created_by=self.admin,
        )
        ContractorInvoice.objects.create(
            invoice_number="INV-1", site=self.site, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(),
            amount=Decimal("1280.00"), status="APPROVED", created_by=self.alex,
        )

    def test_staff_dashboard_shows_real_figures(self):
        for user in (self.admin, self.owner):
            login(self.client, user)
            resp = self.client.get(reverse("ops:dashboard"))
            self.assertEqual(resp.status_code, 200)
            s = resp.context["summary"]
            self.assertEqual(s["revenue"], Decimal("1800.00"))
            self.assertEqual(s["cost"], Decimal("1280.00"))
            self.assertEqual(s["profit"], Decimal("520.00"))
            self.assertEqual(s["services"]["completed"], 1)
            self.assertEqual(s["services"]["scheduled"], 1)
            self.assertContains(resp, "$520.00")

    def test_date_range_filters_money(self):
        login(self.client, self.admin)
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = self.client.get(reverse("ops:dashboard"), {"start": future})
        self.assertEqual(resp.context["summary"]["revenue"], Decimal("0.00"))

    def test_bad_range_is_reported(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:dashboard"), {"start": "2026-10-10", "end": "2026-10-01"})
        self.assertContains(resp, "Start date must be on or before the end date.")

    def test_contractor_gets_own_dashboard(self):
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:dashboard"))
        # Contractors get the approved Contractor Portal.
        self.assertTemplateUsed(resp, "ops/subcontractor_portal.html")
        # Same structure as the ContractorDashboard API (sites / services / invoices / earnings).
        d = resp.context["dashboard"]
        self.assertEqual(d["earnings"]["total_earnings"], Decimal("1280.00"))
        self.assertEqual(d["earnings"]["approved_invoice_count"], 1)
        self.assertEqual(d["sites"]["assigned"], 1)
        self.assertEqual(d["services"]["completed"], 1)
        self.assertNotIn("revenue", d)

    def test_anonymous_redirects_to_login(self):
        resp = self.client.get(reverse("ops:dashboard"))
        self.assertEqual(resp.status_code, 302)


class ClientAccessTests(TestCase):
    def test_owner_can_open_clients(self):
        login(self.client, make_user("OWNER"))
        self.assertEqual(self.client.get(reverse("ops:clients")).status_code, 200)

    def test_client_pages_use_shared_app_shell(self):
        login(self.client, make_user("OWNER"))
        for name in ("ops:clients", "ops:client_create"):
            resp = self.client.get(reverse(name))
            # The approved Clients / Add Client pages use the shared SubSync sidebar + top bar.
            self.assertTemplateUsed(resp, "ops/partials/_sidebar.html")
            self.assertTemplateUsed(resp, "ops/partials/_topbar.html")
            self.assertContains(resp, reverse("ops:client_invoices"))
            self.assertContains(resp, reverse("ops:invoices"))

    def test_reusing_deleted_clients_phone_shows_error_not_500(self):
        login(self.client, make_user("ADMINISTRATOR"))
        # Fields of the approved Add Client form (one "Full name"; role is set server-side).
        data = {"full_name": "Tech", "phone": "0400111222", "email": "a@x.com", "status": "ACTIVE"}
        self.client.post(reverse("ops:client_create"), data)
        from client.model.clientmanage import Client
        Client.objects.get(phone="0400111222").delete()
        resp = self.client.post(reverse("ops:client_create"), {**data, "email": "b@x.com"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "removed client")


class ClientFilterExportTests(TestCase):
    """Clients page status filter (?status=) and CSV export (?format=csv) share one query."""

    def setUp(self):
        from client.model.clientmanage import Client
        self.active = Client.objects.create(first_name="Acme", last_name="Cleaning", phone="0400100001",
                                            email="acme@x.com", role="ADMINISTRATOR", status="ACTIVE")
        self.inactive = Client.objects.create(first_name="Old", last_name="Corp", phone="0400100002",
                                              email="old@x.com", role="ADMINISTRATOR", status="INACTIVE")
        self.other_active = Client.objects.create(first_name="Zeta", phone="0400100003", email="zeta@x.com",
                                                  role="ADMINISTRATOR", status="ACTIVE")
        self.gone = Client.objects.create(first_name="Removed", phone="0400100004", role="ADMINISTRATOR", status="ACTIVE")
        self.gone.delete()  # soft delete
        from client.model.clientmanage import Site
        Site.objects.create(name="Acme HQ", address="1 King William St", cleaning_frequency="WEEKLY",
                            price=Decimal("450.00"), client_id=self.active)
        self.admin = make_user("ADMINISTRATOR")
        login(self.client, self.admin)

    def _listed(self, **params):
        resp = self.client.get(reverse("ops:clients"), params)
        self.assertEqual(resp.status_code, 200)
        return resp, {c.first_name for c in resp.context["page_obj"]}

    def _csv(self, **params):
        resp = self.client.get(reverse("ops:clients"), {**params, "format": "csv"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Type"].startswith("text/csv"))
        self.assertIn("attachment;", resp["Content-Disposition"])
        self.assertRegex(resp["Content-Disposition"], r'filename="clients_\d{4}-\d{2}-\d{2}\.csv"')
        import csv, io
        return list(csv.reader(io.StringIO(resp.content.decode("utf-8-sig"))))

    def test_all_clients_lists_every_live_client(self):
        _, names = self._listed()
        self.assertEqual(names, {"Acme", "Old", "Zeta"})

    def test_status_filters_use_real_values(self):
        self.assertEqual(self._listed(status="ACTIVE")[1], {"Acme", "Zeta"})
        self.assertEqual(self._listed(status="INACTIVE")[1], {"Old"})
        # Unknown values are ignored rather than hiding everything.
        self.assertEqual(self._listed(status="BOGUS")[1], {"Acme", "Old", "Zeta"})

    def test_search_and_filter_combine_and_stay_selected(self):
        resp, names = self._listed(q="a", status="ACTIVE")
        self.assertEqual(names, {"Acme", "Zeta"})
        self.assertContains(resp, '<option value="ACTIVE" selected>Active</option>', html=True)
        self.assertContains(resp, 'value="a"')
        # Export link carries the same search and filter.
        self.assertContains(resp, 'href="?q=a&amp;status=ACTIVE&amp;format=csv"')

    def test_export_matches_filter_and_search(self):
        rows = self._csv()
        self.assertEqual(rows[0], ["Client", "Phone", "Email", "Assigned Sites", "Status"])
        self.assertIn(["Acme Cleaning", "0400100001", "acme@x.com", "1", "Active"], rows)
        self.assertEqual(len(rows), 4)  # header + 3 live clients
        self.assertEqual([r[0] for r in self._csv(status="INACTIVE")[1:]], ["Old Corp"])
        self.assertEqual([r[0] for r in self._csv(q="zeta", status="ACTIVE")[1:]], ["Zeta"])

    def test_export_excludes_soft_deleted_clients(self):
        self.assertNotIn("Removed", [r[0] for r in self._csv()])

    def test_contractor_cannot_view_or_export(self):
        login(self.client, make_user("CONTRACTOR"))
        for params in ({}, {"format": "csv"}):
            resp = self.client.get(reverse("ops:clients"), params)
            self.assertRedirects(resp, reverse("ops:dashboard"), fetch_redirect_response=False)
        self.client.logout()
        resp = self.client.get(reverse("ops:clients"), {"format": "csv"})
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn("text/csv", resp.get("Content-Type", ""))

    def test_status_column_shows_real_status_badges(self):
        resp, _ = self._listed()
        self.assertContains(resp, ">Status</th>")
        self.assertContains(resp, '<span class="pill pill-active">Active</span>', count=2, html=True)
        self.assertContains(resp, '<span class="pill pill-inactive">Inactive</span>', count=1, html=True)

    def test_status_column_handles_blank_and_unexpected_values(self):
        from client.model.clientmanage import Client
        Client.objects.filter(pk=self.other_active.pk).update(status="")
        Client.objects.filter(pk=self.inactive.pk).update(status="ARCHIVED")
        resp, names = self._listed()
        self.assertEqual(names, {"Acme", "Old", "Zeta"})
        self.assertContains(resp, '<span class="pill pill-active">Active</span>', count=1, html=True)
        self.assertNotContains(resp, "pill-inactive")  # no made-up status for the blank one
        self.assertContains(resp, '<span class="pill pill-archived">ARCHIVED</span>', html=True)
