from django.contrib.admin import action
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from invoice.model.invoicemanagement import ContractorInvoice
from client.model.clientmanage import Site
from invoice.api import serializer
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Sum
from datetime import date
from invoice.api import utils

class InvoiceView(GenericAPIView):
    """
    List invoices for the authenticated contractor.

    Results support filtering by site, invoice date, and status, as well as
    site-name search, ordering, and pagination. Invoice status values are
    PENDING, APPROVED, and REJECTED.
    """
    queryset = ContractorInvoice.objects.all()
    serializer_class = serializer.InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["site__name", "invoice_date", "status"]
    ordering_fields = ["invoice_date", "status"]
    search_fields = ["site__name"]


    @extend_schema(tags=["User: Invoice"])
    def post(self, request, *args, **kwargs):
        """
        Create a new invoice for the authenticated contractor.
        """
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not created.",
                error="Only CONTRACTOR users can create invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        site_check = Site.objects.filter(
            id=request.data.get("site"),
            assigned_contractor=request.user,
        ).first()

        if not site_check:
            return project_return(
                message="Not created.",
                error="Invalid site or not assigned to the contractor.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_obj = self.serializer_class(data=request.data)
        if not invoice_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=invoice_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_obj.save(
            created_by=request.user,
        )

        return project_return(
            message="Successfully created.",
            data=self.get_serializer(invoice_obj.instance).data,
            status=status.HTTP_201_CREATED,
        )


    @extend_schema(
        tags=["User: Invoice"],
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
        List invoices for the authenticated contractor with optional filtering,
        searching, and ordering.
        """
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Failed to fetch.",
                error="Only CONTRACTOR can fetch invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        filter_obj = self.filter_queryset(self.get_queryset().filter(created_by=request.user))
        data = self.paginate_queryset(filter_obj)
        invoice_obj = serializer.GetInvoiceSerializer(data, many=True)
        return project_return(
            message="Successfully fetched.",
            data=self.get_paginated_response(invoice_obj.data),
            status=status.HTTP_200_OK,
        )



class DetailInvoiceView(GenericAPIView):
    """
    - Retrieve a specific invoice for the authenticated contractor.
    - Update a specific invoice for the authenticated contractor.
    - Delete a specific invoice for the authenticated contractor.
    """
    queryset = ContractorInvoice.objects.all()
    serializer_class = serializer.InvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["User: Invoice"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Failed to fetch.",
                error="Only CONTRACTOR can fetch invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        invoice = self.get_queryset().filter(id=str(kwargs.get("id")), created_by=request.user).first()
        if not invoice:
            return project_return(
                message="Invalid invoice.",
                error="No invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        invoice_obj = serializer.DetailInvoiceSerializer(invoice)

        return project_return(
            message="Successfully fetched.",
            data=invoice_obj.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=["User: Invoice"])
    def put(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Failed to update.",
                error="Only CONTRACTOR can update invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        invoice = self.get_queryset().filter(id=str(kwargs.get("id")), created_by=request.user).first()
        if not invoice:
            return project_return(
                message="Invalid invoice.",
                error="No invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if invoice.status == "APPROVED":
            return project_return(
                message="Cannot update.",
                error="Approved invoices cannot be updated.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_obj = self.serializer_class(invoice, data=request.data, partial=True)
        if not invoice_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=invoice_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice_obj.save()

        return project_return(
            message="Successfully updated.",
            data=invoice_obj.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=["User: Invoice"])
    def delete(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Failed to delete.",
                error="Only CONTRACTOR can delete invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        invoice = self.get_queryset().filter(id=str(kwargs.get("id")), created_by=request.user).first()
        if not invoice:
            return project_return(
                message="Invalid invoice.",
                error="No invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if invoice.status == "APPROVED":
            return project_return(
                message="Cannot delete.",
                error="Approved invoices cannot be deleted.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.delete()

        return project_return(
            message="Successfully deleted.",
            status=status.HTTP_200_OK,
        )




class TotalEarningsView(GenericAPIView):
    """
    Return the authenticated contractor's approved invoice earnings.

    The response includes the approved invoice count, total amount, and the
    invoice number, ID, amount, and service period for each invoice.
    """
    queryset = ContractorInvoice.objects.all()
    serializer_class = serializer.TotalIncomeSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
            tags=["User: Invoice"],
            parameters=[
                OpenApiParameter(
                    name="start_date",
                    description="Include invoices from this date (YYYY-MM-DD).",
                    required=False,
                    type=date,
                ),
                OpenApiParameter(
                    name="end_date",
                    description="Include invoices through this date (YYYY-MM-DD).",
                    required=False,
                    type=date,
                ),
            ],        
    )
    def get(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Failed to fetch.",
                error="Only CONTRACTOR users can fetch total earnings.",
                status=status.HTTP_403_FORBIDDEN,
            )

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        check_date_format = utils.check_date_format(start_date, end_date)
        
        if check_date_format is False:
            return project_return(
                message="Invalid date format.",
                error="Dates must be in 'YYYY-MM-DD' format.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoices = utils.filter_invoices_by_date_range(
            invoices=self.get_queryset().filter(created_by=request.user, status="APPROVED"),
            start_date=start_date,
            end_date=end_date
        )

        if isinstance(invoices, str):  # Check if the return is an error message
            return project_return(
                message="Invalid date range.",
                error=invoices,
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoices = invoices.order_by("-invoice_date")

        total_income = invoices.aggregate(
            total=Sum("amount")
        )["total"] or 0

        income_data = {
            "invoice_count": invoices.count(),
            "total_income": total_income,
            "invoices": invoices,
        }

        income_obj = self.get_serializer(instance=income_data)

        return project_return(
            message="Successfully fetched total earnings.",
            data=income_obj.data,
            status=status.HTTP_200_OK,
        )