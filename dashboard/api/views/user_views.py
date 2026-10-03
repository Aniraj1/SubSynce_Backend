from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from client.model.clientmanage import Site
from dashboard.api import serializer, utils
from invoice.model.invoicemanagement import ContractorInvoice
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from datetime import date
from decimal import Decimal
from globalutils.returnobject import project_return
from django.db.models import Sum
from schedule.model.cleaningschedule import ServiceSchedule
from work.model.workcomplete import CompleteWork

class ContractorDashboardView(GenericAPIView):
	"""
	- Return the authenticated contractor's dashboard summary.

	- Metrics are limited to the contractor's assigned sites, schedules, work,
	and submitted invoices. Optional dates filter time-based metrics.
	"""

	serializer_class = serializer.ContractorDashboardSerializer
	authentication_classes = [JWTAuthentication]
	permission_classes = [IsAuthenticated]
	throttle_classes = [UserRateThrottle]

	@extend_schema(
		tags=["User: Dashboard"],
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
		if request.user.role != "CONTRACTOR":
			return project_return(
				message="Not allowed.",
				error="Only CONTRACTOR users can view this dashboard.",
				status=status.HTTP_403_FORBIDDEN,
			)

		start_date = request.query_params.get("start_date")
		end_date = request.query_params.get("end_date")

		if not utils.check_date_format(start_date, end_date):
			return project_return(
				message="Invalid date format.",
				error="Dates must be in YYYY-MM-DD format.",
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

		assigned_sites = Site.objects.filter(
			assigned_contractor=request.user
		)
		schedules = ServiceSchedule.objects.filter(
			site__assigned_contractor=request.user
		)
		work_records = CompleteWork.objects.filter(
			completed_by=request.user
		)
		invoices = ContractorInvoice.objects.filter(
			created_by=request.user
		)

		if start:
			schedules = schedules.filter(scheduled_date__gte=start)
			work_records = work_records.filter(schedule__scheduled_date__gte=start)
			invoices = invoices.filter(invoice_date__gte=start)

		if end:
			schedules = schedules.filter(scheduled_date__lte=end)
			work_records = work_records.filter(schedule__scheduled_date__lte=end)
			invoices = invoices.filter(invoice_date__lte=end)

		approved_invoices = invoices.filter(status="APPROVED")
		total_earnings = approved_invoices.aggregate(
			total=Sum("amount")
		)["total"] or Decimal("0.00")

		dashboard_data = {
			"sites": {
				"assigned": assigned_sites.count(),
			},
			"services": {
				"scheduled": schedules.filter(status="SCHEDULED").count(),
				"completed": work_records.filter(status="COMPLETED").count(),
				"in_progress": work_records.filter(status="IN_PROGRESS").count(),
				"missed": work_records.filter(status="MISSED").count(),
				"cancelled": schedules.filter(status="CANCELLED").count(),
			},
			"invoices": {
				"pending": invoices.filter(status="PENDING").count(),
				"approved": approved_invoices.count(),
				"rejected": invoices.filter(status="REJECTED").count(),
			},
			"earnings": {
				"approved_invoice_count": approved_invoices.count(),
				"total_earnings": total_earnings,
			},
		}

		dashboard_serializer = self.get_serializer(instance=dashboard_data)

		return project_return(
			message="Successfully retrieved contractor dashboard data.",
			data=dashboard_serializer.data,
			status=status.HTTP_200_OK,
		)


