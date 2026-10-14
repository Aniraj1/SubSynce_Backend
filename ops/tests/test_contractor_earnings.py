from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from invoice.model.invoicemanagement import ContractorInvoice
from ops import services
from ops.tests.helpers import login, make_site, make_user


def invoice(user, site, day, amount, status="APPROVED", n=[0]):
    n[0] += 1
    return ContractorInvoice.objects.create(
        invoice_number=f"INV-E-{n[0]}", site=site, invoice_date=day, service_period_start=day,
        service_period_end=day, amount=Decimal(amount), created_by=user, status=status,
    )


class ContractorEarningsTests(TestCase):
    def setUp(self):
        self.alex = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)

    def test_earnings_page_is_gone(self):
        with self.assertRaises(NoReverseMatch):
            reverse("ops:my_earnings")
        login(self.client, self.alex)
        self.assertEqual(self.client.get("/my-earnings/").status_code, 404)
        self.assertNotContains(self.client.get(reverse("ops:invoices")), ">Earnings</span>")

    def test_monthly_totals_cover_12_months_and_only_approved(self):
        today = date(2026, 10, 14)
        invoice(self.alex, self.site, date(2026, 10, 2), "300")
        invoice(self.alex, self.site, date(2026, 10, 9), "200")
        invoice(self.alex, self.site, date(2026, 3, 1), "150")
        invoice(self.alex, self.site, date(2026, 9, 1), "999", status="PENDING")
        invoice(self.alex, self.site, date(2025, 10, 31), "50")  # before the 12-month window
        other = make_user("CONTRACTOR")
        invoice(other, make_site(contractor=other), date(2026, 10, 1), "700")
        rows = services.monthly_approved_earnings(self.alex, today=today)
        self.assertEqual(len(rows), 12)
        self.assertEqual(rows[0]["month"], date(2025, 11, 1))
        self.assertEqual(rows[-1]["month"], date(2026, 10, 1))
        self.assertEqual(rows[-1]["total"], Decimal("500"))
        self.assertEqual(rows[4]["total"], Decimal("150"))
        self.assertEqual(sum(r["total"] for r in rows), Decimal("650"))

    def test_my_invoices_shows_graph_and_approved_total(self):
        invoice(self.alex, self.site, date.today(), "400")
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:invoices"))
        self.assertContains(resp, "12-month earnings")
        self.assertContains(resp, "stroke-success")  # rose from last month to this month
        self.assertNotContains(resp, "stroke-error")
        self.assertContains(resp, "From 1 approved invoice<")
        self.assertContains(resp, "$400.00")

    def test_graph_empty_state_and_staff_see_no_graph(self):
        login(self.client, self.alex)
        self.assertContains(self.client.get(reverse("ops:invoices")), "No approved invoices yet.")
        self.client.logout()
        login(self.client, make_user("ADMINISTRATOR"))
        self.assertNotContains(self.client.get(reverse("ops:invoices")), "12-month earnings")

    def test_portal_has_no_alerts_card(self):
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:dashboard"))
        self.assertTemplateUsed(resp, "ops/subcontractor_portal.html")
        self.assertNotContains(resp, "Alerts &amp; Notifications")
        self.assertContains(resp, "Assigned Jobs")

    def test_month_on_month_change_is_green_up_red_down(self):
        from ops.views_invoices import _earnings_chart
        from unittest import mock
        months = [date(2026, m, 1) for m in range(1, 13)]
        totals = [0] * 9 + [100, 300, 120]
        rows = [{"month": m, "total": Decimal(t)} for m, t in zip(months, totals)]
        with mock.patch("ops.services.monthly_approved_earnings", return_value=rows):
            chart = _earnings_chart(self.alex)
        self.assertEqual([s["trend"] for s in chart["segments"]][-3:], ["up", "up", "down"])
        self.assertEqual(chart["segments"][0]["trend"], "flat")
        self.assertEqual(chart["change"], Decimal(-180))
        self.assertEqual(chart["peak"], Decimal(300))

    def test_graph_has_scale(self):
        from ops.views_invoices import _compact_money
        self.assertEqual(_compact_money(Decimal("137920.89")), "$137.9k")
        self.assertEqual(_compact_money(Decimal("1200000")), "$1.2M")
        self.assertEqual(_compact_money(Decimal("950")), "$950")
        self.assertEqual(_compact_money(Decimal("2000")), "$2k")
        invoice(self.alex, self.site, date.today(), "4000")
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:invoices"))
        for label in ("$4k", "$2k", "$0"):
            self.assertContains(resp, f"<span>{label}</span>")


class InvoiceDateRangeTests(TestCase):
    def setUp(self):
        self.alex = make_user("CONTRACTOR")
        site = make_site(contractor=self.alex)
        self.sep = invoice(self.alex, site, date(2026, 9, 10), "100", status="PENDING")
        self.oct = invoice(self.alex, site, date(2026, 10, 5), "200", status="PENDING")
        login(self.client, self.alex)

    def numbers(self, **params):
        resp = self.client.get(reverse("ops:invoices"), params)
        return resp, {i.invoice_number for i in resp.context["page_obj"]}

    def test_from_to_and_open_ended_ranges(self):
        _, found = self.numbers(start="2026-10-01", end="2026-10-31")
        self.assertEqual(found, {self.oct.invoice_number})
        _, found = self.numbers(end="2026-09-30")
        self.assertEqual(found, {self.sep.invoice_number})
        _, found = self.numbers(start="2026-09-10")
        self.assertEqual(found, {self.sep.invoice_number, self.oct.invoice_number})

    def test_reversed_range_shows_error_and_all_invoices(self):
        resp, found = self.numbers(start="2026-10-31", end="2026-10-01")
        self.assertContains(resp, "must be on or before")
        self.assertEqual(len(found), 2)

    def test_bad_date_is_ignored_and_range_kept_in_pagination_links(self):
        _, found = self.numbers(start="not-a-date")
        self.assertEqual(len(found), 2)
        resp, _ = self.numbers(start="2026-09-01", end="2026-10-31")
        self.assertEqual(resp.context["querystring"], "start=2026-09-01&end=2026-10-31")
