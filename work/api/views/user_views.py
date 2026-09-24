from django.contrib.admin import action
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from work.model.workcomplete import CompleteWork, WorkCompleteImage
from client.model.clientmanage import Site
from schedule.model.cleaningschedule import ServiceSchedule
from work.api import serializer
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
    View to handle clock-in and clock-out actions for contractors.
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
    View to handle clock-out actions for contractors.
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