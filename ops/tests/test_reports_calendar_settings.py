from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from ops.models import CompanyProfile
from ops.tests.helpers import login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


class ProfitabilityTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.techcorp = make_site(contractor=self.alex, price="450", name="TechCorp Head Office")
        self.other = make_site(contractor=self.alex, price="190", name="Nexus Office")
        today = date.today()
        for d in range(4):
            job = make_schedule(self.techcorp, self.admin, day=today - timedelta(days=d + 1))
            CompleteWork.objects.create(schedule=job, completed_by=self.alex, status="COMPLETED")
        common = dict(invoice_date=today, service_period_start=today, service_period_end=today)
        ClientInvoice.objects.create(invoice_number="C1", site=self.techcorp, client=self.techcorp.client_id,
                                     amount=Decimal("1800"), status="PAID", created_by=self.admin, **common)
        ClientInvoice.objects.create(invoice_number="C2", site=self.techcorp, client=self.techcorp.client_id,
                                     amount=Decimal("999"), status="ISSUED", created_by=self.admin, **common)
        ContractorInvoice.objects.create(invoice_number="I1", site=self.techcorp, amount=Decimal("1280"),
                                         status="APPROVED", created_by=self.alex, **common)
        ContractorInvoice.objects.create(invoice_number="I2", site=self.techcorp, amount=Decimal("500"),
                                         status="REJECTED", created_by=self.alex, **common)
        ContractorInvoice.objects.create(invoice_number="I3", site=self.other, amount=Decimal("100"),
                                         status="APPROVED", created_by=self.alex, **common)

    def row(self, resp, name):
        return next(r for r in resp.context["rows"] if r["site"].name == name)

    def test_profit_per_site_uses_paid_and_approved_only(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:profitability"))
        tc = self.row(resp, "TechCorp Head Office")
        self.assertEqual((tc["revenue"], tc["cost"], tc["profit"]), (Decimal("1800"), Decimal("1280"), Decimal("520")))
        self.assertEqual(round(tc["margin"], 2), Decimal("0.29"))
        self.assertEqual(tc["completed"], 4)
        self.assertEqual(tc["work_value"], Decimal("1800"))
        nx = self.row(resp, "Nexus Office")
        self.assertEqual(nx["profit"], Decimal("-100"))
        self.assertEqual(resp.context["totals"]["profit"], Decimal("420"))

    def test_client_rollup_and_csv(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:profitability"), {"group": "client"})
        self.assertEqual(len(resp.context["clients"]), 2)
        csv = self.client.get(reverse("ops:profitability"), {"format": "csv"})
        self.assertEqual(csv["Content-Type"], "text/csv")
        self.assertIn(b"TechCorp Head Office", csv.content)

    def test_date_range(self):
        login(self.client, self.admin)
        future = (date.today() + timedelta(days=10)).isoformat()
        resp = self.client.get(reverse("ops:profitability"), {"start": future})
        self.assertEqual(resp.context["totals"]["revenue"], Decimal("0"))

    def test_contractor_forbidden(self):
        login(self.client, self.alex)
        self.assertEqual(self.client.get(reverse("ops:profitability")).status_code, 403)


class CalendarTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.priya = make_user("CONTRACTOR")
        self.alex_site = make_site(contractor=self.alex, name="Alex Site")
        self.priya_site = make_site(contractor=self.priya, name="Priya Site")
        self.day = date.today().replace(day=10)
        self.alex_job = make_schedule(self.alex_site, self.admin, day=self.day)
        self.priya_job = make_schedule(self.priya_site, self.admin, day=self.day)

    def month(self):
        return self.day.strftime("%Y-%m")

    def test_staff_sees_all_jobs_on_the_right_day(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:calendar"), {"month": self.month(), "day": self.day.isoformat()})
        self.assertContains(resp, "Alex Site")
        self.assertContains(resp, "Priya Site")
        cell = next(c for w in resp.context["weeks"] for c in w if c["date"] == self.day)
        self.assertEqual(cell["count"], 2)
        self.assertEqual(len(resp.context["agenda"]), 2)

    def sites_on_day(self, resp):
        cell = next(c for w in resp.context["weeks"] for c in w if c["date"] == self.day)
        return {job.site.name for job in cell["jobs"]}

    def test_staff_filters_by_contractor_and_status(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:calendar"), {"month": self.month(), "contractor": self.alex.pk})
        self.assertEqual(self.sites_on_day(resp), {"Alex Site"})
        CompleteWork.objects.create(schedule=self.alex_job, completed_by=self.alex, status="COMPLETED")
        resp = self.client.get(reverse("ops:calendar"), {"month": self.month(), "status": "COMPLETED"})
        self.assertEqual(self.sites_on_day(resp), {"Alex Site"})

    def test_contractor_sees_only_own_jobs(self):
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:my_calendar"), {"month": self.month()})
        self.assertContains(resp, "Alex Site")
        self.assertNotContains(resp, "Priya Site")

    def test_contractor_cannot_open_all_jobs_calendar(self):
        login(self.client, self.alex)
        self.assertEqual(self.client.get(reverse("ops:calendar")).status_code, 403)

    def test_month_navigation_and_bad_month(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:calendar"), {"month": "2026-12"})
        self.assertEqual(resp.context["next_month"], date(2027, 1, 1))
        self.assertEqual(resp.context["prev_month"], date(2026, 11, 1))
        resp = self.client.get(reverse("ops:calendar"), {"month": "garbage"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["month"], date.today().replace(day=1))


class CompanySettingsTests(TestCase):
    def test_owner_saves_settings_and_terms_prefill_builder(self):
        owner = make_user("OWNER")
        login(self.client, owner)
        resp = self.client.post(reverse("ops:company_settings"), {
            "name": "SubSync Demo Cleaning Co.", "abn": "12 345 678 901", "phone": "08 8000 0000",
            "email": "office@subsync.test", "address": "12 King William St", "default_terms": "Net 7",
        })
        self.assertRedirects(resp, reverse("ops:company_settings"))
        self.assertEqual(CompanyProfile.load().default_terms, "Net 7")
        self.assertEqual(CompanyProfile.objects.count(), 1)
        alex = make_user("CONTRACTOR")
        make_site(contractor=alex)
        self.client.logout()
        login(self.client, alex)
        self.assertContains(self.client.get(reverse("ops:invoice_create")), "Net 7")

    def test_admin_and_contractor_forbidden(self):
        for role in ("ADMINISTRATOR", "CONTRACTOR"):
            login(self.client, make_user(role))
            self.assertEqual(self.client.get(reverse("ops:company_settings")).status_code, 403)
