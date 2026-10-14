from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from invoice.model.invoicemanagement import ContractorInvoice
from ops import services
from ops.models import CompanyProfile, InvoiceLineItem
from ops.tests.helpers import login, make_schedule, make_site, make_user
from work.model.workcomplete import CompleteWork


def builder_post(site, number="INV-2026-001", items=(("Weekly office clean", "4", "320"),), **extra):
    today = date.today()
    data = {
        "invoice_number": number,
        "site": str(site.pk),
        "invoice_date": today.isoformat(),
        "service_period_start": today.replace(day=1).isoformat(),
        "service_period_end": today.isoformat(),
        "notes": "Thanks",
        "terms": "14 days",
        "items-TOTAL_FORMS": str(len(items)),
        "items-INITIAL_FORMS": "0",
        "items-MIN_NUM_FORMS": "1",
        "items-MAX_NUM_FORMS": "50",
    }
    for i, (desc, qty, price) in enumerate(items):
        data.update({f"items-{i}-description": desc, f"items-{i}-quantity": qty, f"items-{i}-unit_price": price})
    data.update(extra)
    return data


class InvoiceBuilderTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.priya = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)

    def test_builder_saves_line_items_and_amount_is_their_sum(self):
        login(self.client, self.alex)
        items = (("Weekly office clean", "4", "320"), ("Carpet add-on", "1", "150"))
        resp = self.client.post(reverse("ops:invoice_create"), builder_post(self.site, items=items))
        inv = ContractorInvoice.objects.get(invoice_number="INV-2026-001")
        self.assertRedirects(resp, reverse("ops:invoice_detail", args=[inv.pk]))
        self.assertEqual(inv.amount, Decimal("1430.00"))
        self.assertEqual(inv.status, "PENDING")
        self.assertEqual(inv.created_by, self.alex)
        self.assertEqual(inv.remarks, "Thanks")
        self.assertEqual(inv.builder.terms, "14 days")
        self.assertEqual([i.description for i in inv.line_items.all()], ["Weekly office clean", "Carpet add-on"])

    def test_builder_page_suggests_next_number_and_default_terms(self):
        CompanyProfile.objects.create(default_terms="Pay in 7 days")
        ContractorInvoice.objects.create(
            invoice_number=f"INV-{date.today().year}-004", site=self.site, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(), amount=1, created_by=self.alex,
        )
        login(self.client, self.alex)
        resp = self.client.get(reverse("ops:invoice_create"))
        self.assertContains(resp, f"INV-{date.today().year}-005")
        self.assertContains(resp, "Pay in 7 days")

    def test_numbering_skips_soft_deleted_invoices(self):
        inv = ContractorInvoice.objects.create(
            invoice_number=f"INV-{date.today().year}-009", site=self.site, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(), amount=1, created_by=self.alex,
        )
        inv.delete()
        self.assertEqual(services.next_invoice_number(), f"INV-{date.today().year}-010")

    def test_duplicate_number_and_bad_period_are_rejected(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        resp = self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        self.assertContains(resp, "already used")
        resp = self.client.post(reverse("ops:invoice_create"), builder_post(
            self.site, number="INV-X", service_period_start=date.today().isoformat(),
            service_period_end=(date.today() - timedelta(days=5)).isoformat()))
        self.assertContains(resp, "must end on or after")
        self.assertEqual(ContractorInvoice.objects.count(), 1)

    def test_zero_total_is_rejected(self):
        login(self.client, self.alex)
        resp = self.client.post(reverse("ops:invoice_create"), builder_post(self.site, items=(("Free", "1", "0"),)))
        self.assertContains(resp, "more than $0.00")
        self.assertFalse(ContractorInvoice.objects.exists())

    def test_contractor_cannot_invoice_unassigned_site(self):
        login(self.client, self.priya)
        resp = self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ContractorInvoice.objects.exists())

    def test_staff_cannot_use_builder(self):
        login(self.client, self.admin)
        self.assertEqual(self.client.get(reverse("ops:invoice_create")).status_code, 403)

    def test_edit_replaces_items_and_recomputes_amount(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        inv = ContractorInvoice.objects.get()
        self.client.post(reverse("ops:invoice_edit", args=[inv.pk]), builder_post(self.site, items=(("Clean", "2", "100"),)))
        inv.refresh_from_db()
        self.assertEqual(inv.amount, Decimal("200.00"))
        self.assertEqual(InvoiceLineItem.objects.filter(invoice=inv).count(), 1)

    def test_decided_invoice_is_locked_for_contractor(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        inv = ContractorInvoice.objects.get()
        inv.status = "APPROVED"
        inv.save()
        self.client.post(reverse("ops:invoice_edit", args=[inv.pk]), builder_post(self.site, items=(("Clean", "2", "100"),)))
        self.client.post(reverse("ops:invoice_delete", args=[inv.pk]))
        inv.refresh_from_db()
        self.assertEqual(inv.amount, Decimal("1280.00"))
        self.assertTrue(ContractorInvoice.objects.filter(pk=inv.pk).exists())

    def test_contractor_sees_only_own_invoices(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        inv = ContractorInvoice.objects.get()
        self.client.logout()
        login(self.client, self.priya)
        self.assertEqual(self.client.get(reverse("ops:invoice_detail", args=[inv.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("ops:invoice_print", args=[inv.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("ops:invoices")), inv.invoice_number)

    def test_print_view_renders_logo_items_and_total(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        inv = ContractorInvoice.objects.get()
        resp = self.client.get(reverse("ops:invoice_print", args=[inv.pk]))
        self.assertContains(resp, "subsync-logo.svg")
        self.assertContains(resp, "Weekly office clean")
        self.assertContains(resp, "$1,280.00")
        self.assertContains(resp, "size: A4")

    def test_gst_unticked_by_default_and_print_has_no_gst_line(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site))
        inv = ContractorInvoice.objects.get()
        self.assertFalse(inv.gst)
        resp = self.client.get(reverse("ops:invoice_print", args=[inv.pk]))
        self.assertNotContains(resp, "GST (10%)")
        self.assertNotContains(resp, "TAX INVOICE")
        self.assertContains(resp, "$1,280.00")

    def test_gst_ticked_keeps_amount_ex_gst_and_print_adds_gst(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site, gst="on"))
        inv = ContractorInvoice.objects.get()
        self.assertTrue(inv.gst)
        self.assertEqual(inv.amount, Decimal("1280.00"))
        for name in ("ops:invoice_print", "ops:invoice_detail"):
            resp = self.client.get(reverse(name, args=[inv.pk]))
            self.assertContains(resp, "Subtotal (ex GST)")
            self.assertContains(resp, "$128.00")
            self.assertContains(resp, "$1,408.00")
        self.assertContains(self.client.get(reverse("ops:invoice_print", args=[inv.pk])), "TAX INVOICE")

    def test_edit_shows_and_can_untick_gst(self):
        login(self.client, self.alex)
        self.client.post(reverse("ops:invoice_create"), builder_post(self.site, gst="on"))
        inv = ContractorInvoice.objects.get()
        self.assertContains(self.client.get(reverse("ops:invoice_edit", args=[inv.pk])), 'id="id_gst" value="on" class="w-4 h-4 accent-[#F27E22]" checked')
        self.client.post(reverse("ops:invoice_edit", args=[inv.pk]), builder_post(self.site))
        inv.refresh_from_db()
        self.assertFalse(inv.gst)

    def test_gst_rounds_to_the_cent(self):
        inv = ContractorInvoice(amount=Decimal("10.05"), gst=True)
        self.assertEqual(services.invoice_totals(inv), {
            "subtotal": Decimal("10.05"), "gst": Decimal("1.01"), "total": Decimal("11.06"),
        })
        self.assertIsNone(services.invoice_totals(ContractorInvoice(amount=Decimal("10.05")))["gst"])


class VerificationTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.owner = make_user("OWNER")
        self.alex = make_user("CONTRACTOR")
        self.priya = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)
        self.today = date.today()

    def _invoice(self, qty="1", by=None, number="INV-1"):
        inv = ContractorInvoice.objects.create(
            invoice_number=number, site=self.site, invoice_date=self.today,
            service_period_start=self.today - timedelta(days=10), service_period_end=self.today,
            amount=Decimal("320") * Decimal(qty), created_by=by or self.alex,
        )
        InvoiceLineItem.objects.create(invoice=inv, description="Clean", quantity=Decimal(qty), unit_price=Decimal("320"))
        return inv

    def _done(self, days_ago, by=None):
        job = make_schedule(self.site, self.admin, day=self.today - timedelta(days=days_ago))
        CompleteWork.objects.create(schedule=job, completed_by=by or self.alex, status="COMPLETED")
        return job

    def codes(self, inv):
        return [code for code, _ in services.verify_invoice(inv)["flags"]]

    def test_clean_invoice_has_no_flags(self):
        self._done(3)
        self.assertEqual(self.codes(self._invoice()), [])

    def test_no_recorded_work(self):
        make_schedule(self.site, self.admin, day=self.today - timedelta(days=2))
        self.assertIn("NO_RECORDED_WORK", self.codes(self._invoice()))

    def test_missing_visits(self):
        self._done(3)
        make_schedule(self.site, self.admin, day=self.today - timedelta(days=1))
        flags = services.verify_invoice(self._invoice())["flags"]
        self.assertIn(("MISSING_VISITS", "1 of 2 scheduled services were recorded as completed."), flags)

    def test_work_outside_period_does_not_count(self):
        self._done(30)
        self.assertIn("NO_RECORDED_WORK", self.codes(self._invoice()))

    def test_period_boundary_counts(self):
        self._done(10)  # exactly the period start
        self.assertEqual(self.codes(self._invoice()), [])

    def test_wrong_contractor(self):
        self._done(3)
        self._done(4, by=self.priya)
        self.assertIn("WRONG_CONTRACTOR", self.codes(self._invoice()))

    def test_billed_quantity_exceeds_recorded(self):
        self._done(3)
        self.assertIn("QUANTITY_EXCEEDS_WORK", self.codes(self._invoice(qty="3")))

    def test_duplicate_period(self):
        self._done(3)
        self._invoice(number="INV-A")
        self.assertIn("DUPLICATE_PERIOD", self.codes(self._invoice(number="INV-B")))

    def test_cancelled_jobs_are_ignored(self):
        self._done(3)
        make_schedule(self.site, self.admin, day=self.today - timedelta(days=1), status="CANCELLED")
        self.assertEqual(self.codes(self._invoice()), [])

    def test_detail_shows_flags_to_staff_only(self):
        inv = self._invoice()
        login(self.client, self.admin)
        self.assertContains(self.client.get(reverse("ops:invoice_detail", args=[inv.pk])), "No completed services are recorded")
        login(self.client, self.alex)
        self.assertNotContains(self.client.get(reverse("ops:invoice_detail", args=[inv.pk])), "No completed services are recorded")

    def test_approve_records_reviewer_and_counts_as_cost(self):
        self._done(3)
        inv = self._invoice()
        login(self.client, self.owner)
        self.client.post(reverse("ops:invoice_decide", args=[inv.pk]), {"decision": "APPROVED"})
        inv.refresh_from_db()
        self.assertEqual(inv.status, "APPROVED")
        self.assertEqual(inv.verified_by, self.owner)
        self.assertIsNotNone(inv.verified_at)
        self.assertEqual(services.admin_summary()["cost"], Decimal("320.00"))

    def test_reject_requires_reason(self):
        inv = self._invoice()
        login(self.client, self.admin)
        resp = self.client.post(reverse("ops:invoice_decide", args=[inv.pk]), {"decision": "REJECTED"})
        self.assertEqual(resp.status_code, 400)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "PENDING")
        self.client.post(reverse("ops:invoice_decide", args=[inv.pk]), {"decision": "REJECTED", "verification_notes": "No work recorded"})
        inv.refresh_from_db()
        self.assertEqual(inv.status, "REJECTED")
        self.assertEqual(services.admin_summary()["cost"], Decimal("0.00"))

    def test_decision_is_final(self):
        inv = self._invoice()
        login(self.client, self.admin)
        self.client.post(reverse("ops:invoice_decide", args=[inv.pk]), {"decision": "REJECTED", "verification_notes": "x"})
        self.client.post(reverse("ops:invoice_decide", args=[inv.pk]), {"decision": "APPROVED"})
        inv.refresh_from_db()
        self.assertEqual(inv.status, "REJECTED")

    def test_contractor_cannot_decide(self):
        inv = self._invoice()
        login(self.client, self.alex)
        self.assertEqual(self.client.post(reverse("ops:invoice_decide", args=[inv.pk]), {"decision": "APPROVED"}).status_code, 403)
