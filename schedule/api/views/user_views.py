from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from schedule.model.cleaningschedule import ServiceSchedule
from client.model.clientmanage import Site
from schedule.api import serializer
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return
from schedule.api.utils import schedule_date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone



class UserScheduleView(GenericAPIView):
    """
    API endpoint that allows users to view their cleaning schedules.
    """
    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.DetailScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["site__name", "scheduled_date", "status"]
    ordering_fields = ["scheduled_date", "status"]
    search_fields = ["site__name", "notes"]

    @extend_schema(
        tags=["User: Service Schedule"],
        parameters=[
            OpenApiParameter(
                name="q",
                description="Filter by site name",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="scheduled_date",
                description="Filter by scheduled date (YYYY-MM-DD)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="status",
                description="Filter by status (e.g. Cancelled, completed)",
                required=False,
                type=str,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve the list of cleaning schedules for the authenticated user.
        """
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not created.",
                error="Only Contractors can view their cleaning schedules.",
                status=status.HTTP_403_FORBIDDEN,
            )

        filter_obj = self.filter_queryset(self.get_queryset().filter(site__assigned_contractor=str(request.user.id)))


        data = self.paginate_queryset(filter_obj)
        schedule_obj = self.serializer_class(data, many=True)
        return project_return(
            message="User cleaning schedules retrieved successfully.",
            data=self.get_paginated_response(schedule_obj.data),
            status=status.HTTP_200_OK,
        )


class GetDetailScheduleView(GenericAPIView):
    """
    API endpoint that allows users to view the details of a specific cleaning schedule.
    """
    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.DetailScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["User: Service Schedule"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not fetched.",
                error="Only CONTRACTOR can fetch their own schedules.",
                status=status.HTTP_403_FORBIDDEN,
            )

        schedule = self.get_queryset().filter(id=kwargs.get("id"), site__assigned_contractor=str(request.user.id)).first()
        if schedule is None:
            return project_return(
                message="Invalid data.",
                error="Schedule not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        schedule_obj = self.serializer_class(schedule)
        
        return project_return(
            message="Successfully fetched.",
            data=schedule_obj.data,
            status=status.HTTP_200_OK,
        )


class UserScheduleSummaryView(GenericAPIView):
    """
    API endpoint that allows users to view a summary of their cleaning schedules.
    """
    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.DetailScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["User: Dashboard"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not fetched.",
                error="Only CONTRACTOR can fetch their own schedule summary.",
                status=status.HTTP_403_FORBIDDEN,
            )

        today = timezone.now().date()
        upcoming_schedules = self.get_queryset().filter(site__assigned_contractor=str(request.user.id), scheduled_date__gte=today, status="SCHEDULED")
        completed_schedules = self.get_queryset().filter(site__assigned_contractor=str(request.user.id), status="COMPLETED")
        missed_schedules = self.get_queryset().filter(site__assigned_contractor=str(request.user.id), status="MISSED")

        summary_data = {
            "upcoming_count": upcoming_schedules.count(),
            "completed_count": completed_schedules.count(),
            "missed_count": missed_schedules.count(),
        }

        return project_return(
            message="Successfully fetched schedule summary.",
            data=summary_data,
            status=status.HTTP_200_OK,
        )


SCHEDULE_STATUS = (
    ("SCHEDULED", "SCHEDULED"),
    ("COMPLETED", "COMPLETED"),
    ("MISSED", "MISSED"),
    ("CANCELLED", "CANCELLED"),
)