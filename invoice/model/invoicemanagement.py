import uuid
from django.db import models
from authuser.model.softdeletemodel import BaseModel
from client.model.clientmanage import Client, Site
from authuser.model.user import User
from django.core.validators import MinValueValidator





CONTRACTOR_INVOICE_STATUS = (
    ("PENDING", "PENDING"),
    ("APPROVED", "APPROVED"),
    ("REJECTED", "REJECTED"),
)

CLIENT_INVOICE_STATUS = (
    ("ISSUED", "ISSUED"),
    ("PAID", "PAID"),
    ("OVERDUE", "OVERDUE"),
    ("CANCELLED", "CANCELLED"),
)



class ContractorInvoice(BaseModel):
    """
    Invoice submitted by a contractor for cleaning services at a site.
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    invoice_number = models.CharField(max_length=255, unique=True, db_column="INVOICE_NUMBER")
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name="site_invoice_contractor",
        db_column="SITE_ID",
    )
    invoice_date = models.DateField(db_column="INVOICE_DATE")
    service_period_start = models.DateField(
        db_column="SERVICE_PERIOD_START",
    )
    service_period_end = models.DateField(
        db_column="SERVICE_PERIOD_END",
    )
    gst = models.BooleanField(
            default=False,
            db_column="GST",
        )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        db_column="AMOUNT",
    )
    status = models.CharField(
        max_length=20,
        choices=CONTRACTOR_INVOICE_STATUS,
        default="PENDING",
        db_column="STATUS",
    )
    verification_notes = models.TextField(
        blank=True,
        null=True,
        db_column="VERIFICATION_NOTES",
    )
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="verified_invoices",
        db_column="VERIFIED_BY",
    )
    verified_at = models.DateTimeField(
        blank=True,
        null=True,
        db_column="VERIFIED_AT",
    )
    remarks = models.TextField(
        blank=True,
        null=True,
        db_column="NOTES",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_invoices_contractor",
        db_column="SUBMITTED_BY",
    )

    
    class Meta:
        db_table = "POC_CONTRACTOR_INVOICE"

    def __str__(self):
        return f"{self.id} \t {self.invoice_number} \t {self.site.name}"



class ClientInvoice(BaseModel):
    id = models.UUIDField(
            primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
        )
    invoice_number = models.CharField(max_length=255, unique=True, db_column="INVOICE_NUMBER")
    site = models.ForeignKey(
        Site,
        on_delete=models.PROTECT,
        related_name="site_invoice_client",
        db_column="SITE_ID",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="client_invoices",
        db_column="CLIENT_ID",
    )
    invoice_date = models.DateField(db_column="INVOICE_DATE")
    service_period_start = models.DateField(
        db_column="SERVICE_PERIOD_START",
    )
    service_period_end = models.DateField(
        db_column="SERVICE_PERIOD_END",
    )
    gst = models.BooleanField(
        default=False,
        db_column="GST",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        db_column="AMOUNT",
    )
    status = models.CharField(
        max_length=20,
        choices=CLIENT_INVOICE_STATUS,
        default="ISSUED",
        db_column="STATUS",
    )
    remarks = models.TextField(
        blank=True,
        null=True,
        db_column="NOTES",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_invoice_client",
        db_column="CREATED_BY",
    )

    
    class Meta:
        db_table = "POC_CLIENT_INVOICE"

    def __str__(self):
        return f"{self.id} \t {self.invoice_number} \t {self.site.name}"
