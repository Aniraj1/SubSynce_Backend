from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from client.model.clientmanage import Site
from invoice.api import serializer, utils
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone
from datetime import  date
from django.db.models import Sum
from decimal import Decimal




class AllInvoiceAdminView(GenericAPIView):
    """
    - List all invoice records for administrators.

    - Results support filtering by site, invoice date, and status, as well as
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
    - Retrieve one invoice record for administrators.

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
    - Verify an invoice for administrators.
    - Only invoices with a PENDING status can be verified.
    - The verification process updates the invoice status and records the verifier and timestamp.
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
    

class TotalExpenditureAdminView(GenericAPIView):
    """
    - Retrieve total expenditure for administrators.
    - Expenditure is calculated as the total amount from approved contractor invoices.
    - Optional query parameters:
        - start_date: Include invoices from this date (YYYY-MM-DD).
        - end_date: Include invoices through this date (YYYY-MM-DD).
    """
    queryset = ContractorInvoice.objects.all()
    serializer_class = serializer.TotalExpenditureSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        tags=["Admin: Invoice"],
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
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Failed to fetch.",
                error="Only ADMINISTRATOR can fetch total expenditure.",
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
            invoices=self.get_queryset().filter(status="APPROVED"),
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

        total_expenditure = invoices.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        expenditure_data = {
            "invoice_count": invoices.count(),
            "total_expenditure": total_expenditure,
            "invoices": invoices,
        }

        expenditure_obj = self.get_serializer(instance=expenditure_data)

        return project_return(
            message="Successfully fetched total expenditure.",
            data=expenditure_obj.data,
            status=status.HTTP_200_OK,
        )
        

class ClientInvoiceViews(GenericAPIView):
    """
    - Retrieve all client invoices (GET)
    - Create a new client invoice (POST)
    """
    queryset = ClientInvoice.objects.all()
    serializer_class = serializer.ClientInvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["site__name", "invoice_date", "status"]
    ordering_fields = ["invoice_date", "status"]
    search_fields = ["site__name", "client__first_name"]


    @extend_schema(tags=["Admin: Client Invoice"])
    def post(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can create client invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        site_client = Site.objects.filter(
            id=request.data.get("site"),
            client_id=request.data.get("client"),
        ).first()

        if not site_client:
            return project_return(
                message="Not created.",
                error="The specified site does not belong to the specified client.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_invoice_obj = self.serializer_class(data=request.data)

        if not client_invoice_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=client_invoice_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_invoice_obj.save(
            created_by=request.user,
        )

        return project_return(
            message="Successfully created.",
            data=self.get_serializer(client_invoice_obj.instance).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
            tags=["Admin: Client Invoice"],
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
                    description="Search by site name, or client first name.",
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
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can view client invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        filter_obj = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(filter_obj)
        client_invoice_obj = serializer.ClientInvoiceDetailSerializer(data, many=True)
        return project_return(
            message="Successfully fetched.",
            data=self.get_paginated_response(client_invoice_obj.data),
            status=status.HTTP_200_OK,
        )


class DetailClientInvoiceView(GenericAPIView):
    """
    - Retrieve one client invoice record for administrators.
    - Update one client invoice record for administrators.
    """
    queryset = ClientInvoice.objects.all()
    serializer_class = serializer.ClientInvoiceSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Admin: Client Invoice"])
    def put(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can update client invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_invoice = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not client_invoice:
            return project_return(
                message="Invalid client invoice.",
                error="No client invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if client_invoice.status != "ISSUED":
            return project_return(
                message="Invalid client invoice.",
                error="Only ISSUED client invoices can be updated.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_invoice_obj = self.serializer_class(client_invoice, data=request.data, partial=True)
        if not client_invoice_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=client_invoice_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_invoice_obj.save()

        return project_return(
            message="Successfully updated.",
            data=self.get_serializer(client_invoice_obj.instance).data,
            status=status.HTTP_200_OK,
        )


    @extend_schema(tags=["Admin: Client Invoice"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can view client invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_invoice = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not client_invoice:
            return project_return(
                message="Invalid client invoice.",
                error="No client invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        client_invoice_obj = serializer.ClientInvoiceDetailSerializer(client_invoice)

        return project_return(
            message="Successfully fetched.",
            data=client_invoice_obj.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=["Admin: Client Invoice"])
    def delete(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can delete client invoices.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_invoice = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not client_invoice:
            return project_return(
                message="Invalid client invoice.",
                error="No client invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if client_invoice.status != "ISSUED":
            return project_return(
                message="Invalid client invoice.",
                error="Only ISSUED client invoices can be deleted.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_invoice.delete()

        return project_return(
            message="Successfully deleted.",
            data=None,
            status=status.HTTP_204_NO_CONTENT,
        )


class ClientInvoiceStatusUpdateView(GenericAPIView):
    """
    - Update the status of a client invoice (PUT)
    - Only ADMINISTRATOR users can update the status.
    """
    queryset = ClientInvoice.objects.all()
    serializer_class = serializer.ClientInvoiceStatusUpdateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Admin: Client Invoice"])
    def put(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can update client invoice status.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_invoice = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not client_invoice:
            return project_return(
                message="Invalid client invoice.",
                error="No client invoice found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        client_invoice_obj = self.serializer_class(client_invoice, data=request.data, partial=True)
        if not client_invoice_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=client_invoice_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_invoice_obj.save()

        return project_return(
            message="Successfully updated.",
            data=self.get_serializer(client_invoice_obj.instance).data,
            status=status.HTTP_200_OK,
        )



class RevenueReportView(GenericAPIView):
    """
    - Retrieve total revenue from a specific client for administrators.
    - Revenue is calculated as the total amount from paid client invoices.
    - Optional query parameters:
        - client_id: Filter by a specific client ID.
        - start_date: Include invoices from this date (YYYY-MM-DD).
        - end_date: Include invoices through this date (YYYY-MM-DD).
    """
    queryset = ClientInvoice.objects.all()
    serializer_class = serializer.RevenueFromClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        tags=["Admin: Client Invoice"],
        parameters=[
            OpenApiParameter(
                name="client_id",
                description="Filter by client ID.",
                required=False,
                type=str,
            ),
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
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can view revenue from clients.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_id = request.query_params.get("client_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")


        check_date_format = utils.check_date_format(start_date, end_date)
        
        if check_date_format is False:
            return project_return(
                message="Invalid date format.",
                error="Dates must be in 'YYYY-MM-DD' format.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoices = self.get_queryset().filter(status="PAID")
        if client_id:
            invoices = invoices.filter(client_id=client_id)

        invoices = utils.filter_invoices_by_date_range(
            invoices=invoices,
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


        total_revenue = invoices.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        revenue_data = {
            "invoice_count": invoices.count(),
            "total_revenue": total_revenue,
            "invoices": invoices,
        }

        revenue_obj = self.get_serializer(instance=revenue_data)

        return project_return(
            message="Successfully retrieved revenue data.",
            data=revenue_obj.data,
            status=status.HTTP_200_OK,
        )

class ProfitReportView(GenericAPIView):
    """
    - Retrieve total profit for administrators.
    - Profit is calculated as total revenue from paid client invoices minus total expenditure from approved contractor invoices.
    - Optional query parameters:
        - start_date: Include invoices from this date (YYYY-MM-DD).
    """
    queryset = ClientInvoice.objects.all()
    serializer_class = serializer.ProfitReportSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        tags=["Admin: Profit"],
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
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not allowed.",
                error="Only ADMINISTRATOR can view total profit.",
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
            invoices=self.get_queryset().filter(status="PAID"),
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

        total_revenue = invoices.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        total_expenditure = ContractorInvoice.objects.filter(
            status="APPROVED"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        profit = total_revenue - total_expenditure

        profit_data = {
            "total_expenditure": total_expenditure,
            "total_revenue": total_revenue,
            "profit": profit,
        }

        profit_obj = self.get_serializer(instance=profit_data)

        return project_return(
            message="Successfully retrieved profit data.",
            data=profit_obj.data,
            status=status.HTTP_200_OK,
        )