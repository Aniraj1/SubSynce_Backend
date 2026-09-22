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



class ServiceScheduleView(GenericAPIView):
    """
    Create and list service schedules for administrators.
    """
    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.ServiceScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ["scheduled_date", "status", "site_id"]
    ordering = ["scheduled_date", "scheduled_time"]

    @extend_schema(tags=["Service Schedule"])
    def post(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not created.",
                error="Only ADMINISTRATOR can create Service Schedule.",
                status=status.HTTP_403_FORBIDDEN,
            )

        site = Site.objects.filter(id=str(request.data.get("site"))).first()
        if not site:
            return project_return(
                message="Not created.",
                error="Site does not exist.",
                status=status.HTTP_404_NOT_FOUND,
            )
        if not site.assigned_contractor:
            return project_return(
                message="Not created.",
                error="Site does not have assigned contractor.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule_obj = self.serializer_class(data=request.data)
        if not schedule_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=schedule_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        schedule = schedule_obj.save(created_by=request.user)

        return project_return(
            message="Successfully created.",
            data=self.get_serializer(schedule).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=["Service Schedule"], parameters=[
            OpenApiParameter(
                name="ordering",
                description=(
                    "Order by scheduled_date, status, site_id."
                ),
                required=False,
                type=str,
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve all service schedules.
        """
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch service schedules.",
                status=status.HTTP_403_FORBIDDEN,
            )
        filter_obj = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(filter_obj)
        schedule_obj = self.serializer_class(data, many=True)
        return project_return(
            message="Successfully fetched.",
            data=self.get_paginated_response(schedule_obj.data),
            status=status.HTTP_200_OK,
        )

class ServiceScheduleDetailView(GenericAPIView):
    """
    Retrieve, update, and cancel an individual service schedule.

    Only administrators can manage service schedules.
    """
    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.ChangeServiceScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Service Schedule"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch service schedules.",
                status=status.HTTP_403_FORBIDDEN,
            )

        schedule = self.get_queryset().filter(id=kwargs.get("id")).first()
        if schedule is None:
            return project_return(
                message="Invalid data.",
                error="Schedule not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        schedule_obj = serializer.DetailScheduleSerializer(schedule)
        
        return project_return(
            message="Successfully fetched.",
            data=schedule_obj.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(tags=["Service Schedule"])
    def put(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not updated.",
                error="Only ADMINISTRATOR can update service schedules.",
                status=status.HTTP_403_FORBIDDEN,
            )
        schedule = self.get_queryset().filter(id=kwargs.get("id")).first()

        if schedule is None:
            return project_return(
                message="Not updated.",
                error="Schedule not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        site = Site.objects.filter(id=str(request.data.get("site"))).first()
        if not site:
            return project_return(
                message="Not updated.",
                error="Site does not exist.",
                status=status.HTTP_404_NOT_FOUND,
            )
        if not site.assigned_contractor:
            return project_return(
                message="Not created.",
                error="Site does not have assigned contractor.",
                status=status.HTTP_400_BAD_REQUEST,
            )


        schedule_obj = self.serializer_class(schedule, data=request.data, partial=True)
        if not schedule_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=schedule_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


        schedule_obj.save()
        return project_return(
            message="Successfully updated.",
            data=self.get_serializer(schedule).data,
            status=status.HTTP_200_OK,
        )


    @extend_schema(tags=["Service Schedule"])
    def delete(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not cancelled.",
                error="Only ADMINISTRATOR can cancel service schedules.",
                status=status.HTTP_403_FORBIDDEN,
            )

        schedule = self.get_queryset().filter(id=kwargs.get("id")).first()
        if schedule is None:
            return project_return(
                message="Not cancelled.",
                error="Schedule not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        schedule.status = "CANCELLED"
        schedule.save()
        return project_return(
            message="Successfully cancelled.",
            status=status.HTTP_200_OK,
        )



class ChangeStatusView(GenericAPIView):
    """
    Change the status of a service schedule.

    Only administrators can change schedule status.
    """

    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.ChangeStatusSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]


    @extend_schema(tags=["Service Schedule"])
    def patch(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not updated.",
                error="Only ADMINISTRATOR can update service schedule status.",
                status=status.HTTP_403_FORBIDDEN,
            )
        schedule = self.get_queryset().filter(id=kwargs.get("id")).first()

        if schedule is None:
            return project_return(
                message="Not updated.",
                error="Schedule not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        schedule_obj = self.serializer_class(schedule, data=request.data, partial=True)
        if not schedule_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=schedule_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        schedule_obj.save()
        return project_return(
            message="Successfully updated.",
            data=self.get_serializer(schedule).data,
            status=status.HTTP_200_OK,
        )


class ScheduleSummary(GenericAPIView):
    """
    Return summary counts for all service schedules.

    Only administrators can retrieve the schedule summary.
    """

    queryset = ServiceSchedule.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Admin: Dashboard"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch the schedule summary.",
                status=status.HTTP_403_FORBIDDEN,
            )

        schedule_obj = self.get_queryset()
        today = timezone.localdate()

        summary = {
            "total_schedules": schedule_obj.count(),
            "scheduled": schedule_obj.filter(status="SCHEDULED").count(),
            "completed": schedule_obj.filter(status="COMPLETED").count(),
            "missed": schedule_obj.filter(status="MISSED").count(),
            "cancelled": schedule_obj.filter(status="CANCELLED").count(),
            "today_schedules": schedule_obj.filter(scheduled_date=today).count(),
            "upcoming_schedules": schedule_obj.filter(scheduled_date__gt=today).count(),
        }

        return project_return(
            message="Successfully fetched.",
            data=summary,
            status=status.HTTP_200_OK,
        )