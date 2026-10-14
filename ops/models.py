"""Frontend-owned data that the backend has no place for yet.

The backend's ContractorInvoice and ClientInvoice each store one total amount.
The invoice builders keep their line items, notes and payment terms here,
linked to that invoice, and always write the sum of the line items back into
the invoice's amount so the backend's reports and API stay correct.
"""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from django.conf import settings

from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice


class InvoiceExtra(models.Model):
    invoice = models.OneToOneField(ContractorInvoice, on_delete=models.CASCADE, related_name="builder")
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Builder data for {self.invoice.invoice_number}"


class LineItemBase(models.Model):
    position = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        abstract = True
        ordering = ["position", "id"]

    @property
    def total(self):
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"


class InvoiceLineItem(LineItemBase):
    invoice = models.ForeignKey(ContractorInvoice, on_delete=models.CASCADE, related_name="line_items")

    class Meta(LineItemBase.Meta):
        pass


class ClientInvoiceExtra(models.Model):
    """Builder data for an invoice sent to a client, plus who last changed its status."""

    invoice = models.OneToOneField(ClientInvoice, on_delete=models.CASCADE, related_name="builder")
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
    )
    status_changed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Builder data for {self.invoice.invoice_number}"


class ClientInvoiceLineItem(LineItemBase):
    invoice = models.ForeignKey(ClientInvoice, on_delete=models.CASCADE, related_name="line_items")

    class Meta(LineItemBase.Meta):
        pass


class CompanyProfile(models.Model):
    """Single row: business details printed on invoices, plus an optional uploaded logo."""

    name = models.CharField(max_length=120, default="SubSync")
    abn = models.CharField("ABN", max_length=30, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    default_terms = models.TextField(blank=True, default="Payment within 14 days.")
    logo = models.ImageField(upload_to="company_logo/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def load(cls):
        profile, _ = cls.objects.get_or_create(pk=1)
        return profile

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
