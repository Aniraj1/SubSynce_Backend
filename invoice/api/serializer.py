from rest_framework import serializers

from authuser.model.user import User
from client.model.clientmanage import Site, Client
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

class UserSerializer(serializers.ModelSerializer):
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
    verified_by = UserSerializer(read_only=True)
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



class InvoiceAdminSerializer(serializers.ModelSerializer):
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
            "status",
            "verification_notes",
            "verified_by",
            "verified_at",
            "remarks",
            "created_by",
        ]

class DetailInvoiceAdminSerializer(serializers.ModelSerializer):
    verified_by = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
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
            "status",
            "verification_notes",
            "verified_by",
            "verified_at",
            "remarks",
            "created_by",
        ]

class InvoiceVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorInvoice
        fields = [
            "status",
            "verification_notes"
        ]




class ExpenditureInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorInvoice
        fields = [
            "id",
            "invoice_number",
            "amount",
            "status",
            "service_period_start",
            "service_period_end",
        ]



class TotalExpenditureSerializer(serializers.Serializer):
    invoice_count = serializers.IntegerField()
    total_expenditure = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    invoices = ExpenditureInvoiceSerializer(many=True)

class TotalIncomeSerializer(serializers.Serializer):
    invoice_count = serializers.IntegerField()
    total_income = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    invoices = ExpenditureInvoiceSerializer(many=True)


class ClientInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoice
        fields = [
            "id",
            "invoice_number",
            "invoice_date",
            "site",
            "client",
            "invoice_date",
            "service_period_start",
            "service_period_end",
            "amount",
            "remarks",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_by",
        ]


class clientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id",
            "first_name"
        ]

class ClientInvoiceDetailSerializer(serializers.ModelSerializer):
    site = SiteInvoiceSerializer(read_only=True)
    client = clientSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    class Meta:
        model = ClientInvoice
        fields = [
            "id",
            "invoice_number",
            "site",
            "client",
            "invoice_date",
            "service_period_start",
            "service_period_end",
            "amount",
            "remarks",
            "status",
            "created_by",
        ]

class ClientInvoiceStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoice
        fields = [
            "status"
        ]



class ClientInvoiceDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoice
        fields = [
            "id",
            "invoice_number",
            "amount",
            "status",
            "service_period_start",
            "service_period_end",
        ]

class RevenueFromClientSerializer(serializers.Serializer):
    invoice_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    invoices = ClientInvoiceDetailsSerializer(many=True)

class ProfitReportSerializer(serializers.Serializer):
    total_expenditure = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    total_revenue = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    profit = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
    )