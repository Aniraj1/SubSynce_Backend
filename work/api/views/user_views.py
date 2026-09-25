from django.contrib.admin import action
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from work.model.workcomplete import CompleteWork, WorkCompleteImage
from client.model.clientmanage import Site
from schedule.model.cleaningschedule import ServiceSchedule
from work.api import serializer, utils
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone
from django.db import transaction



class ClockInView(GenericAPIView):
    """
    Start a scheduled cleaning service for the assigned contractor.

    A contractor can clock in only once for a scheduled service assigned to
    them.
    """
    queryset = CompleteWork.objects.all()
    serializer_class = serializer.ClockInSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["User: Work"])
    def post(self, request, *args, **kwargs):
        """
        Handle clock-in actions.
        """
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not created.",
                error="Only CONTRACTOR users can clock in.",
                status=status.HTTP_403_FORBIDDEN,
            )
        schedule = ServiceSchedule.objects.filter(
            id=request.data.get("schedule"),
            site__assigned_contractor=request.user,
            status="SCHEDULED",
        ).first()
        if not schedule:
            return project_return(
                message="Invalid schedule.",
                error="No scheduled service found for this contractor.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if self.get_queryset().filter(schedule=schedule).exists():
            return project_return(
                message="Not created.",
                error="Work has already been started for this schedule.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        clock_in_obj = self.serializer_class(data=request.data)
        if not clock_in_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=clock_in_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        work = clock_in_obj.save(
            schedule=schedule,
            completed_by=request.user,
            check_in_time=timezone.now(),
        )
        
        return project_return(
            message="Successfully created.",
            data=self.get_serializer(work).data,
            status=status.HTTP_201_CREATED,
        )

class ClockOutView(GenericAPIView):
    """
    Complete an active cleaning service for the assigned contractor.

    The endpoint records the check-out time, completion notes, location, and
    any evidence images uploaded with the request.
    """
    queryset = CompleteWork.objects.all()
    serializer_class = serializer.ClockOutSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["User: Work"])
    def patch(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not updated.",
                error="Only CONTRACTOR users can clock out.",
                status=status.HTTP_403_FORBIDDEN,
            )
        
        work = self.get_queryset().filter(
            id=str(kwargs.get("id")),
            completed_by=request.user,
            check_out_time__isnull=True,
        ).first()
        if not work:
            return project_return(
                message="Invalid work.",
                error="No active work found for this schedule.",
                status=status.HTTP_404_NOT_FOUND,
            )

        images = request.FILES.getlist("images")

        data = request.data.copy()
        data.pop("images", None)

        clock_out_obj = self.serializer_class(work, data=data, partial=True)

        if not clock_out_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=clock_out_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            work = clock_out_obj.save(
                check_out_time=timezone.now(),
                status="COMPLETED",
            )
            for image in images:
                WorkCompleteImage.objects.create(
                    work_completion=work,
                    evidence_photo=image,
                )
        

        return project_return(
            message="Successfully updated.",
            data=self.get_serializer(work).data,
            status=status.HTTP_200_OK,
        )


class UserWorkView(GenericAPIView):
    """
    List the authenticated contractor's work-completion records.

    Results support status/date filtering, period filtering, text search,
    ordering, and pagination. Work status values are IN_PROGRESS, COMPLETED,
    and MISSED.
    """
    queryset = CompleteWork.objects.all()
    serializer_class = serializer.WorkCompleteDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['status', "schedule__scheduled_date"]
    ordering_fields = ["check_in_time", "check_out_time", "status"]
    ordering = ["-check_in_time"]
    search_fields = ["schedule__site__name", "location", "completion_notes"]

    @extend_schema(
        tags=["User: Work"],
        parameters=[
            OpenApiParameter(
                name="status",
                description=(
                    "Filter by work status: IN_PROGRESS, COMPLETED, or MISSED."
                ),
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="schedule__scheduled_date",
                description="Filter by scheduled date (YYYY-MM-DD).",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="q",
                description="Search by site name, location, or completion notes.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Order by check-in time, check-out time, or status. Use '-' for descending order.",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="period",
                description="Filter work by today or the current calendar week.",
                type=str,
                required=False,
                enum=["today", "weekly"],
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not fetched.",
                error="Only CONTRACTOR users can fetch their own work details.",
                status=status.HTTP_403_FORBIDDEN,
            )
        
        work_obj = self.get_queryset().filter(completed_by=request.user)
        
        filter_by_date = utils.filter_work_by_period(
            work_obj, request.query_params.get("period")
        )
        if filter_by_date is not None:
            work_obj = filter_by_date
        
        
        filter_obj = self.filter_queryset(work_obj)

        data = self.paginate_queryset(filter_obj)
        schedule_obj = self.serializer_class(data, many=True)
        return project_return(
            message="retrieved successfully.",
            data=self.get_paginated_response(schedule_obj.data),
            status=status.HTTP_200_OK,
        )


class GetDetailWorkView(GenericAPIView):
    """
    Retrieve one work-completion record belonging to the contractor.

    A record owned by another contractor is treated as not found.
    """
    queryset = CompleteWork.objects.all()
    serializer_class = serializer.DetailWorkSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["User: Work"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Not fetched.",
                error="Only CONTRACTOR can fetch their own work details.",
                status=status.HTTP_403_FORBIDDEN,
            )
        
        work = self.get_queryset().filter(
            id=str(kwargs.get("id")),
            completed_by=request.user,
        ).first()

        if not work:
            return project_return(
                message="Invalid work.",
                error="No work found for this ID.",
                status=status.HTTP_404_NOT_FOUND,
            )

        work_obj = self.serializer_class(work)

        return project_return(
            message="retrieved successfully.",
            data=work_obj.data,
            status=status.HTTP_200_OK,
        )