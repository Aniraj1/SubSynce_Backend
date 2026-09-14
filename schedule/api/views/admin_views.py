from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema
from schedule.model.cleaningschedule import ServiceSchedule, ScheduleAssignment, ServiceOccurrence
from client.model.clientmanage import Site
from schedule.api import serializer
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return
from schedule.api.utils import schedule_date

SCHEDULE_STATUS = ["ACTIVE", "INACTIVE", "CANCELLED"]
SCHEDULE_FREQUENCY = ["ONCE", "DAILY", "WEEKLY", "MONTHLY"]


class ServiceScheduleView(GenericAPIView):
    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.ServiceScheduleSerializer
    authentication_classes = [JWTAuthentication]
    perission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Service Schedule"])
    def post(self, request, *args, **kwargs):
        """
        Create a new service schedule.
        """
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not created.",
                error="Only ADMINISTRATOR can create CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )

        check_site = Site.objects.filter(id=request.data.get("site")).first()
        if check_site is None:
            return project_return(
                message="Not created.",
                error="Site does not exist.",
                status=status.HTTP_404_NOT_FOUND,
            )
        
        schedule_obj = self.serializer_class(data=request.data)
        if not schedule_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=schedule_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        check_date = schedule_date(
            request.data.get("start_date"), 
            request.data.get("end_date"), 
            request.data.get("frequency")
            )

        if check_date is not None:
            return project_return(
                message="Invalid data.",
                error=check_date,
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = schedule_obj.save(created_by=request.user)

        return project_return(
            message="Successfully created.",
            data=self.get_serializer(schedule).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(tags=["Service Schedule"])
    def get(self, request, *args, **kwargs):
        """
        Retrieve all service schedules.
        """
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch CLIENT.",
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
    - update service schedule by id
    - delete service schedule by id
    - get service schedule by id
    - only ADMINISTRATOR can update service schedule
    """
    queryset = ServiceSchedule.objects.all()
    serializer_class = serializer.ServiceScheduleSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["Service Schedule"])
    def put(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not updated.",
                error="Only ADMINISTRATOR can update CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )

        check_site = Site.objects.filter(id=str(request.data.get("site"))).first()
        if check_site is None:
            return project_return(
                message="Not created.",
                error="Site does not exist.",
                status=status.HTTP_404_NOT_FOUND,
            )
        if str(request.user.id) != str(request.data.get("created_by")):
            return project_return(
                message="Not updated.",
                error="created_by field cannot be updated.",
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.data.get("status") not in SCHEDULE_STATUS:
            return project_return(
                message="Not updated.",
                error="Invalid status.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.data.get("frequency") not in SCHEDULE_FREQUENCY:
            return project_return(
                message="Not updated.",
                error="Invalid frequency.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        schedule = self.get_queryset().filter(id=kwargs.get("id")).first()
        if schedule is None:
            return project_return(
                message="Invalid data.",
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

        check_date = schedule_date(
            request.data.get("start_date"), 
            request.data.get("end_date"), 
            request.data.get("frequency")
            )

        if check_date is not None:
            return project_return(
                message="Invalid data.",
                error=check_date,
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
                message="Not deleted.",
                error="Only ADMINISTRATOR can delete CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )

        schedule = self.get_queryset().filter(id=kwargs.get("id")).first()
        if schedule is None:
            return project_return(
                message="Invalid data.",
                error="Schedule not found.",
                status=status.HTTP_404_NOT_FOUND,
            )
        
        schedule.delete()
        return project_return(
            message="Successfully deleted.",
            status=status.HTTP_200_OK,
        )


    @extend_schema(tags=["Service Schedule"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch CLIENT.",
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

