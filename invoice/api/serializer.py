from rest_framework import serializers

from authuser.model.user import User
from client.model.clientmanage import Site
from invoice.model.invoicemanagement import ContractorInvoice, ClientInvoice
from work.model.workcomplete import CompleteWork, WorkCompleteImage



class InvoiceSerializer(serializers.ModelSerializer):
    site_name = serializers.CharField(source="site.name", read_only=True)
    class Meta:
        model = ContractorInvoice
        fields = [
            "id",
            "invoice_number",
            "site",
            "site_name",
            "invoice_date",
            "service_period_start",
            "service_period_end",
            "amount",
            "remarks",
            "status",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "status",
            "site_name",
        ]

class SiteInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = [
            "id",
            "name"
        ]

class VerifiedBySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username"
        ]

class GetInvoiceSerializer(serializers.ModelSerializer):
    site = SiteInvoiceSerializer(read_only=True)
    class Meta:
        model = ContractorInvoice
        fields = [
            "id",
            "invoice_number",
            "site",
            "invoice_date",
            "service_period_start",
            "service_period_end",
            "amount",
            "remarks",
            "status",
        ]

class DetailInvoiceSerializer(serializers.ModelSerializer):
    verified_by = VerifiedBySerializer(read_only=True)
    site = SiteInvoiceSerializer(read_only=True)
    class Meta:
        model = ContractorInvoice
        fields = [
            "id",
            "invoice_number",
            "site",
            "invoice_date",
            "service_period_start",
            "service_period_end",
            "amount",
            "remarks",
            "status",
            "verification_notes",
            "verified_by",
            "verified_at",
        ]