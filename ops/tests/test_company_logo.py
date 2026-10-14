import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from ops.forms import CompanyProfileForm
from ops.models import CompanyProfile
from ops.tests.helpers import login, make_user

MEDIA = tempfile.mkdtemp()
DETAILS = {
    "name": "SubSync Demo Cleaning Co.", "abn": "", "phone": "", "email": "",
    "address": "", "default_terms": "Net 7",
}


def png(name="logo.png"):
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "teal").save(buf, format="PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA)
class CompanyLogoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        login(self.client, make_user("OWNER"))
        self.url = reverse("ops:company_settings")

    def test_upload_shows_logo_and_replacing_deletes_old_file(self):
        resp = self.client.post(self.url, {**DETAILS, "logo": png("first.png")})
        self.assertRedirects(resp, self.url)
        first = CompanyProfile.load().logo
        self.assertTrue(first.name.startswith("company_logo/"))
        self.assertContains(self.client.get(self.url), first.url)

        self.client.post(self.url, {**DETAILS, "logo": png("second.png")})
        self.assertFalse(first.storage.exists(first.name))
        self.assertTrue(CompanyProfile.load().logo.name.endswith(".png"))

    def test_saving_without_a_file_keeps_logo_and_clear_removes_it(self):
        self.client.post(self.url, {**DETAILS, "logo": png()})
        name = CompanyProfile.load().logo.name
        self.client.post(self.url, DETAILS)
        self.assertEqual(CompanyProfile.load().logo.name, name)

        self.client.post(self.url, {**DETAILS, "logo-clear": "on"})
        self.assertFalse(CompanyProfile.load().logo)
        self.assertContains(self.client.get(self.url), "images/subsync-logo.svg")

    def test_rejects_non_image_and_oversized_logo(self):
        bad = SimpleUploadedFile("notes.txt", b"hello", content_type="text/plain")
        resp = self.client.post(self.url, {**DETAILS, "logo": bad})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["form"].errors["logo"])

        big = png()
        big.size = 3 * 1024 * 1024
        form = CompanyProfileForm(DETAILS, {"logo": big}, instance=CompanyProfile.load())
        self.assertFalse(form.is_valid())
        self.assertIn("2MB", " ".join(form.errors["logo"]))
        self.assertFalse(CompanyProfile.load().logo)


@override_settings(MEDIA_ROOT=MEDIA)
class InvoiceLogoTests(TestCase):
    def test_printed_invoice_uses_uploaded_logo(self):
        from datetime import date

        from invoice.model.invoicemanagement import ContractorInvoice
        from ops.tests.helpers import make_site

        owner = make_user("OWNER")
        contractor = make_user("CONTRACTOR")
        site = make_site(contractor=contractor)
        inv = ContractorInvoice.objects.create(
            invoice_number="INV-LOGO-1", site=site, invoice_date=date.today(),
            service_period_start=date.today(), service_period_end=date.today(),
            amount=100, created_by=contractor,
        )
        print_url = reverse("ops:invoice_print", args=[inv.pk])
        login(self.client, owner)
        self.assertContains(self.client.get(print_url), "images/subsync-logo.svg")

        self.client.post(reverse("ops:company_settings"), {**DETAILS, "logo": png()})
        resp = self.client.get(print_url)
        self.assertContains(resp, CompanyProfile.load().logo.url)
        self.assertNotContains(resp, "images/subsync-logo.svg")
