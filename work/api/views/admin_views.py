from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from work.model.workcomplete import CompleteWork
from client.model.clientmanage import Site
from work.api import serializer
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.utils import timezone
from datetime import timedelta



class AllWorkCompleteView(GenericAPIView):
    """
    List all work-completion records for administrators.

    Results support filtering by site, scheduled date, and status, as well as
    site-name search, ordering, and pagination. Work status values are
    IN_PROGRESS, COMPLETED, and MISSED.
    """
    queryset = CompleteWork.objects.all()
    serializer_class = serializer.WorkSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["schedule__site__name", "schedule__scheduled_date", "status"]
    ordering_fields = ["schedule__scheduled_date", "status"]
    ordering = ["-schedule__scheduled_date"]
    search_fields = ["schedule__site__name"]

    @extend_schema(
        tags=["Admin: Work"],
        parameters=[
            OpenApiParameter(
                name="schedule__site__name",
                description="Filter by exact site name.",
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
                name="status",
                description=(
                    "Filter by work status: IN_PROGRESS, COMPLETED, or MISSED."
                ),
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
                description=(
                    "Order by schedule__scheduled_date "
                    "Prefix with '-' for descending order."
                ),
                required=False,
                type=str,
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        Return the filtered and paginated work-completion list.
        """
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Access denied.",
                error="Only ADMINISTRATOR can view completed work.",
                status=status.HTTP_403_FORBIDDEN,
            )

        filter_obj = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(filter_obj)
        work_obj = self.serializer_class(data, many=True)
        
        return project_return(
            message="Completed work entries retrieved successfully.",
            data=self.get_paginated_response(work_obj.data),
            status=status.HTTP_200_OK,
        )

class WorkCompleteDetailView(GenericAPIView):
    """
    Retrieve one work-completion record by ID for an administrator.
    """
    queryset = CompleteWork.objects.all()
    serializer_class = serializer.DetailWorkSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["User: Admin"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch work details.",
                status=status.HTTP_403_FORBIDDEN,
            )
        
        work = self.get_queryset().filter(
            id=str(kwargs.get("id"))
        ).first()

        if not work:
            return project_return(
                message="Invalid work.",
                error="No work found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        work_obj = self.serializer_class(work)

        return project_return(
            message="retrieved successfully.",
            data=work_obj.data,
            status=status.HTTP_200_OK,
        )


class AdminWorkSummaryView(GenericAPIView):
    """
    Return work-completion counts for the administrator dashboard.

    The response includes total, status-based, today-completed, and
    current-week-completed counts.
    """
    queryset = CompleteWork.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Admin: Dashboard"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Access denied.",
                error="Only ADMINISTRATOR can view work summary.",
                status=status.HTTP_403_FORBIDDEN,
            )

        work_obj = self.get_queryset()
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        summary = {
            "total_work": work_obj.count(),
            "in_progress": work_obj.filter(
                status="IN_PROGRESS"
            ).count(),
            "completed": work_obj.filter(
                status="COMPLETED"
            ).count(),
            "missed": work_obj.filter(
                status="MISSED"
            ).count(),
            "today_completed": work_obj.filter(
                status="COMPLETED",
                schedule__scheduled_date=today,
            ).count(),
            "this_week_completed": work_obj.filter(
                status="COMPLETED",
                schedule__scheduled_date__range=[
                    week_start,
                    week_end,
                ],
            ).count(),
        }

        return project_return(
            message="Work summary retrieved successfully.",
            data=summary,
            status=status.HTTP_200_OK,
        )