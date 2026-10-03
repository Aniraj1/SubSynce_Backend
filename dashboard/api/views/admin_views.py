from drf_spectacular.utils import extend_schema, OpenApiParameter
from invoice.model.invoicemanagement import ClientInvoice, ContractorInvoice
from client.model.clientmanage import Client, Site
from authuser.model.user import User
from rest_framework.generics import GenericAPIView
from dashboard.api import serializer, utils
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

from schedule.model.cleaningschedule import ServiceSchedule
from work.model.workcomplete import CompleteWork


class AdminDashboardView(GenericAPIView):
    """
    Return the consolidated administrator dashboard summary.

    Optional date and site filters apply to service and financial metrics.
    Client, site, and contractor totals are global counts.
    """

    serializer_class = serializer.AdminDashboardSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        tags=["Admin: Dashboard"],
        parameters=[
            OpenApiParameter(
            name="start_date",
            description="Include records from this date (YYYY-MM-DD).",
            required=False,
            type=date,
            ),
            OpenApiParameter(
            name="end_date",
            description="Include records through this date (YYYY-MM-DD).",
            required=False,
            type=date,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
            message="Not allowed.",
            error="Only ADMINISTRATOR users can view the dashboard.",
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

        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None

        if start and end and start > end:
            return project_return(
                message="Invalid date range.",
                error="start_date cannot be after end_date.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedules = ServiceSchedule.objects.all()
        work_records = CompleteWork.objects.all()
        contractor_invoices = ContractorInvoice.objects.all()
        client_invoices = ClientInvoice.objects.all()

        if start:
            schedules = schedules.filter(scheduled_date__gte=start)
            work_records = work_records.filter(schedule__scheduled_date__gte=start)
            contractor_invoices = contractor_invoices.filter(invoice_date__gte=start)
            client_invoices = client_invoices.filter(invoice_date__gte=start)

        if end:
            schedules = schedules.filter(scheduled_date__lte=end)
            work_records = work_records.filter(schedule__scheduled_date__lte=end)
            contractor_invoices = contractor_invoices.filter(invoice_date__lte=end)
            client_invoices = client_invoices.filter(invoice_date__lte=end)

        approved_contractor_invoices = contractor_invoices.filter(status="APPROVED")
        revenue_invoices = client_invoices.filter(status="PAID")

        total_expenditure = approved_contractor_invoices.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")
        total_revenue = revenue_invoices.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        dashboard_data = {
            "clients": {
                "total": Client.objects.count(),
            },
            "sites": {
                "total": Site.objects.count(),
            },
            "contractors": {
                "total": User.objects.filter(role="CONTRACTOR").count(),
            },
            "services": {
                "scheduled": schedules.filter(status="SCHEDULED").count(),
                "completed": work_records.filter(status="COMPLETED").count(),
                "in_progress": work_records.filter(status="IN_PROGRESS").count(),
                "missed": work_records.filter(status="MISSED").count(),
                "cancelled": schedules.filter(status="CANCELLED").count(),
            },
            "contractor_invoices": {
                "pending": contractor_invoices.filter(status="PENDING").count(),
                "approved": approved_contractor_invoices.count(),
                "rejected": contractor_invoices.filter(status="REJECTED").count(),
                "total_expenditure": total_expenditure,
            },
            "client_invoices": {
                "issued": client_invoices.filter(status="ISSUED").count(),
                "paid": client_invoices.filter(status="PAID").count(),
                "overdue": client_invoices.filter(status="OVERDUE").count(),
                "cancelled": client_invoices.filter(status="CANCELLED").count(),
                "total_revenue": total_revenue,
            },
            "profitability": {
                "profit": total_revenue - total_expenditure,
            },
        }

        dashboard_serializer = self.get_serializer(instance=dashboard_data)

        return project_return(
            message="Successfully retrieved dashboard data.",
            data=dashboard_serializer.data,
            status=status.HTTP_200_OK,
        )


