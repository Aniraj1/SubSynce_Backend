from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from client.model.clientmanage import Site
from invoice.api import serializer
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone
from datetime import timedelta


class AllInvoiceAdminView(GenericAPIView):
    """
    List all invoice records for administrators.

    Results support filtering by site, invoice date, and status, as well as
    site-name search, ordering, and pagination. Invoice status values are
    PENDING, PAID, and OVERDUE.
    """
    queryset = ContractorInvoice.objects.all()
    serializer_class = serializer.InvoiceAdminSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["site__name", "invoice_date", "status"]
    ordering_fields = ["invoice_date", "status"]
    search_fields = ["site__name"]

    @extend_schema(
        tags=["Admin: Invoice"],
        parameters=[
            OpenApiParameter(
                name="status",
                description=(
                    "Filter by work status: PENDING, APPROVED, or REJECTED."
                ),
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="site__name",
                description="Filter by exact site name.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="q",
                description="Search by site name.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Order by invoice_date or status. Use '-' for descending order.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="invoice_date",
                description="Filter by invoice date (YYYY-MM-DD).",
                required=False,
                type=str,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        List invoices for the authenticated administrator with optional filtering,
        searching, and ordering.
        """
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Failed to fetch.",
                error="Only ADMINISTRATOR can fetch invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        filter_obj = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(filter_obj)
        invoice_obj = self.serializer_class(data, many=True)
        return project_return(
            message="Successfully fetched.",
            data=self.get_paginated_response(invoice_obj.data),
            status=status.HTTP_200_OK,
        )

class GetDetailInvoiceAdminView(GenericAPIView):
    """
    Retrieve one invoice record for administrators.
    """
    queryset = ContractorInvoice.objects.all()
    serializer_class = serializer.DetailInvoiceAdminSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Admin: Invoice"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Failed to fetch.",
                error="Only ADMINISTRATOR can fetch invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        invoice = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not invoice:
            return project_return(
                message="Invalid invoice.",
                error="No invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        invoice_obj = self.serializer_class(invoice)

        return project_return(
            message="Successfully fetched.",
            data=invoice_obj.data,
            status=status.HTTP_200_OK,
        )

class InvoiceVerificationView(GenericAPIView):
    """
    Verify an invoice for administrators.
    """
    queryset = ContractorInvoice.objects.all()
    serializer_class = serializer.InvoiceVerificationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Admin: Invoice"])
    def patch(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Failed to verify.",
                error="Only ADMINISTRATOR can verify invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )
            

        invoice = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not invoice:
            return project_return(
                message="Invalid invoice.",
                error="No invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if invoice.status != "PENDING":
            return project_return(
                message="Cannot verify.",
                error="Only PENDING invoices can be verified.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_obj = self.serializer_class(invoice, data=request.data, partial=True)
        if not invoice_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=invoice_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_obj.save(verified_by=request.user, verified_at=timezone.now())

        return project_return(
            message="Successfully verified.",
            data=self.get_serializer(invoice).data,
            status=status.HTTP_200_OK,
        )