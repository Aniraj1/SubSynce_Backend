from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from ops import services
from ops.models import CompanyProfile
from ops.tests.helpers import login, make_schedule, make_site, make_user
from ops.tests.test_invoices import builder_post
from work.model.workcomplete import CompleteWork

YEAR = date.today().year


def make_client_invoice(site, by, number=None, amount="900.00", status="ISSUED"):
    today = date.today()
    return ClientInvoice.objects.create(
        invoice_number=number or services.next_client_invoice_number(), site=site, client=site.client_id,
        invoice_date=today, service_period_start=today.replace(day=1), service_period_end=today,
        amount=Decimal(amount), status=status, created_by=by,
    )


class ClientInvoiceAccessTests(TestCase):
    def setUp(self):
        self.owner = make_user("OWNER")
        self.admin = make_user("ADMINISTRATOR")
        self.alex = make_user("CONTRACTOR")
        self.site = make_site(contractor=self.alex)
        self.invoice = make_client_invoice(self.site, self.admin)

    def test_admin_and_owner_can_open_every_page(self):
        for user in (self.admin, self.owner):
            login(self.client, user)
            for name, args in (
                ("ops:client_invoices", []), ("ops:client_invoice_create", []),
                ("ops:client_invoice_detail", [self.invoice.pk]), ("ops:client_invoice_edit", [self.invoice.pk]),
                ("ops:client_invoice_print", [self.invoice.pk]),
            ):
                self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 200, (user.role, name))

    def test_contractor_is_forbidden(self):
        login(self.client, self.alex)
        self.assertEqual(self.client.get(reverse("ops:client_invoices")).status_code, 403)
        self.assertEqual(self.client.get(reverse("ops:client_invoice_detail", args=[self.invoice.pk])).status_code, 403)
        resp = self.client.post(reverse("ops:client_invoice_status", args=[self.invoice.pk]), {"status": "PAID"})
        self.assertEqual(resp.status_code, 403)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "ISSUED")

    def test_anonymous_goes_to_login(self):
        resp = self.client.get(reverse("ops:client_invoices"))
        self.assertEqual(resp.status_code, 302)

    def test_sidebar_keeps_client_and_contractor_invoices_apart(self):
        login(self.client, self.admin)
        resp = self.client.get(reverse("ops:dashboard"))
        self.assertContains(resp, reverse("ops:client_invoices"))
        self.assertContains(resp, "Client Invoices")
        self.assertContains(resp, "Contractor Invoices")
        login(self.client, self.alex)
        self.assertNotContains(self.client.get(reverse("ops:dashboard")), reverse("ops:client_invoices"))


class ClientInvoiceBuilderTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.owner = make_user("OWNER")
        self.site = make_site(price="320.00")
        login(self.client, self.admin)

    def test_create_takes_client_from_site_and_amount_is_line_total(self):
        items = (("Weekly office clean", "4", "320"), ("Window add-on", "1", "150"))
        resp = self.client.post(reverse("ops:client_invoice_create"),
                                builder_post(self.site, number=f"CINV-{YEAR}-001", items=items))
        inv = ClientInvoice.objects.get(invoice_number=f"CINV-{YEAR}-001")
        self.assertRedirects(resp, reverse("ops:client_invoice_detail", args=[inv.pk]))
        self.assertEqual(inv.client, self.site.client_id)
        self.assertEqual(inv.amount, Decimal("1430.00"))
        self.assertEqual(inv.status, "ISSUED")
        self.assertEqual(inv.created_by, self.admin)
        self.assertEqual(inv.remarks, "Thanks")
        self.assertEqual(inv.builder.terms, "14 days")
        self.assertEqual([i.description for i in inv.line_items.all()], ["Weekly office clean", "Window add-on"])

    def test_gst_tick_box_is_saved_and_printed(self):
        self.client.post(reverse("ops:client_invoice_create"),
                         builder_post(self.site, number=f"CINV-{YEAR}-001", gst="on"))
        inv = ClientInvoice.objects.get(invoice_number=f"CINV-{YEAR}-001")
        self.assertTrue(inv.gst)
        self.assertEqual(inv.amount, Decimal("1280.00"))
        resp = self.client.get(reverse("ops:client_invoice_print", args=[inv.pk]))
        self.assertContains(resp, "TAX INVOICE")
        self.assertContains(resp, "$128.00")
        self.assertContains(resp, "$1,408.00")
        self.client.post(reverse("ops:client_invoice_edit", args=[inv.pk]), builder_post(self.site, number=inv.invoice_number))
        inv.refresh_from_db()
        self.assertFalse(inv.gst)
        self.assertNotContains(self.client.get(reverse("ops:client_invoice_print", args=[inv.pk])), "GST (10%)")

    def test_owner_can_create(self):
        login(self.client, self.owner)
        self.client.post(reverse("ops:client_invoice_create"), builder_post(self.site, number="CINV-OWN-1"))
        self.assertEqual(ClientInvoice.objects.get(invoice_number="CINV-OWN-1").created_by, self.owner)

    def test_new_page_suggests_cinv_number_and_default_terms(self):
        CompanyProfile.objects.create(default_terms="Pay in 7 days")
        make_client_invoice(self.site, self.admin, number=f"CINV-{YEAR}-004")
        resp = self.client.get(reverse("ops:client_invoice_create"))
        self.assertContains(resp, f"CINV-{YEAR}-005")
        self.assertContains(resp, "Pay in 7 days")

    def test_site_in_query_prefills_price(self):
        resp = self.client.get(reverse("ops:client_invoice_create") + f"?site={self.site.pk}")
        self.assertContains(resp, 'value="320.00"')
        self.assertEqual(self.client.get(reverse("ops:client_invoice_create") + "?site=nope").status_code, 200)

    def test_numbering_is_separate_from_contractor_invoices_and_skips_soft_deleted(self):
        ContractorInvoice.objects.create(
            invoice_number=f"INV-{YEAR}-007", site=self.site, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(), amount=1, created_by=self.admin,
        )
        self.assertEqual(services.next_client_invoice_number(), f"CINV-{YEAR}-001")
        make_client_invoice(self.site, self.admin, number=f"CINV-{YEAR}-009").delete()
        self.assertEqual(services.next_client_invoice_number(), f"CINV-{YEAR}-010")

    def test_duplicate_number_bad_period_and_zero_total_are_rejected(self):
        make_client_invoice(self.site, self.admin, number="CINV-DUP")
        resp = self.client.post(reverse("ops:client_invoice_create"), builder_post(self.site, number="cinv-dup"))
        self.assertContains(resp, "already used")
        resp = self.client.post(reverse("ops:client_invoice_create"), builder_post(
            self.site, number="CINV-X", service_period_start=date.today().isoformat(),
            service_period_end=date(2000, 1, 1).isoformat(),
        ))
        self.assertContains(resp, "end on or after")
        resp = self.client.post(reverse("ops:client_invoice_create"),
                                builder_post(self.site, number="CINV-Y", items=(("Free", "1", "0"),)))
        self.assertContains(resp, "more than $0.00")
        self.assertEqual(ClientInvoice.objects.count(), 1)

    def test_edit_rewrites_lines_and_can_move_to_another_clients_site(self):
        inv = make_client_invoice(self.site, self.admin, number="CINV-E")
        other = make_site(price="100.00")
        resp = self.client.post(reverse("ops:client_invoice_edit", args=[inv.pk]),
                                builder_post(other, number="CINV-E", items=(("Deep clean", "2", "100"),)))
        self.assertRedirects(resp, reverse("ops:client_invoice_detail", args=[inv.pk]))
        inv.refresh_from_db()
        self.assertEqual(inv.site, other)
        self.assertEqual(inv.client, other.client_id)
        self.assertEqual(inv.amount, Decimal("200.00"))
        self.assertEqual(inv.line_items.count(), 1)

    def test_only_issued_invoices_can_be_edited_or_deleted(self):
        paid = make_client_invoice(self.site, self.admin, number="CINV-P", status="PAID")
        resp = self.client.post(reverse("ops:client_invoice_edit", args=[paid.pk]), builder_post(self.site, number="CINV-P"))
        self.assertRedirects(resp, reverse("ops:client_invoice_detail", args=[paid.pk]))
        self.client.post(reverse("ops:client_invoice_delete", args=[paid.pk]))
        self.assertTrue(ClientInvoice.objects.filter(pk=paid.pk).exists())

        issued = make_client_invoice(self.site, self.admin, number="CINV-I")
        resp = self.client.post(reverse("ops:client_invoice_delete", args=[issued.pk]))
        self.assertRedirects(resp, reverse("ops:client_invoices"))
        self.assertFalse(ClientInvoice.objects.filter(pk=issued.pk).exists())


class ClientInvoiceStatusTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.site = make_site()
        self.invoice = make_client_invoice(self.site, self.admin)
        login(self.client, self.admin)

    def set_status(self, status, invoice=None):
        invoice = invoice or self.invoice
        self.client.post(reverse("ops:client_invoice_status", args=[invoice.pk]), {"status": status})
        invoice.refresh_from_db()
        return invoice.status

    def test_issued_to_overdue_to_paid_records_who(self):
        self.assertEqual(self.set_status("OVERDUE"), "OVERDUE")
        self.assertEqual(self.set_status("PAID"), "PAID")
        self.assertEqual(self.invoice.builder.status_changed_by, self.admin)
        self.assertIsNotNone(self.invoice.builder.status_changed_at)

    def test_paid_and_cancelled_are_final(self):
        self.assertEqual(self.set_status("PAID"), "PAID")
        self.assertEqual(self.set_status("CANCELLED"), "PAID")
        other = make_client_invoice(self.site, self.admin)
        self.assertEqual(self.set_status("CANCELLED", other), "CANCELLED")
        self.assertEqual(self.set_status("PAID", other), "CANCELLED")

    def test_unknown_status_is_ignored(self):
        self.assertEqual(self.set_status("APPROVED"), "ISSUED")

    def test_requires_post(self):
        resp = self.client.get(reverse("ops:client_invoice_status", args=[self.invoice.pk]))
        self.assertEqual(resp.status_code, 405)

    def test_paid_invoice_counts_as_revenue(self):
        self.set_status("PAID")
        row = next(r for r in services.site_profitability() if r["site"] == self.site)
        self.assertEqual(row["revenue"], Decimal("900.00"))


class ClientInvoiceListTests(TestCase):
    def setUp(self):
        self.admin = make_user("ADMINISTRATOR")
        self.site = make_site(name="Harbour Tower")
        self.other = make_site(name="Rundle Mall")
        make_client_invoice(self.site, self.admin, number="CINV-A", amount="100.00")
        make_client_invoice(self.site, self.admin, number="CINV-B", amount="250.00", status="OVERDUE")
        make_client_invoice(self.other, self.admin, number="CINV-C", amount="400.00", status="PAID")
        login(self.client, self.admin)

    def test_totals(self):
        resp = self.client.get(reverse("ops:client_invoices"))
        self.assertContains(resp, "$350.00")  # outstanding: issued + overdue
        self.assertContains(resp, "2 unpaid")
        self.assertContains(resp, "$400.00")  # paid

    def test_status_filter_and_search(self):
        resp = self.client.get(reverse("ops:client_invoices"), {"status": "PAID"})
        self.assertEqual([i.invoice_number for i in resp.context["page_obj"]], ["CINV-C"])
        resp = self.client.get(reverse("ops:client_invoices"), {"q": "harbour"})
        self.assertEqual({i.invoice_number for i in resp.context["page_obj"]}, {"CINV-A", "CINV-B"})
        resp = self.client.get(reverse("ops:client_invoices"), {"q": self.other.client_id.first_name})
        self.assertEqual([i.invoice_number for i in resp.context["page_obj"]], ["CINV-C"])

    def test_detail_shows_work_value_and_print_shows_bill_to(self):
        inv = ClientInvoice.objects.get(invoice_number="CINV-A")
        job = make_schedule(self.site, self.admin, day=date.today())
        CompleteWork.objects.create(schedule=job, completed_by=make_user("CONTRACTOR"), status="COMPLETED")
        resp = self.client.get(reverse("ops:client_invoice_detail", args=[inv.pk]))
        self.assertContains(resp, "1 completed job ")
        self.assertContains(resp, "Mark as Paid")
        resp = self.client.get(reverse("ops:client_invoice_print", args=[inv.pk]))
        self.assertContains(resp, "Bill to")
        self.assertContains(resp, self.site.client_id.first_name)
