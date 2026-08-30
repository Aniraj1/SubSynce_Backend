from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from client.model import clientmanage
from client.api import serializer
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from globalutils.returnobject import project_return


class AddClientView(GenericAPIView):
    """
    - Client register using first_name, last_name, phone, email
    - Only ADMINISTRATOR can create CLIENT
    """

    queryset = clientmanage.Client
    serializer_class = serializer.ClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["client"])
    def post(self, request, *args, **kwargs):
        client_obj = self.serializer_class(data=request.data)
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not created.",
                error="Only ADMINISTRATOR can create CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )
        if client_obj.is_valid():
            check_email = clientmanage.Client.objects.filter(
                email=request.data.get("email")
            )
            if check_email:
                return project_return(
                    message="Not created.",
                    error="Client with this email already exists.",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            client_obj.save()
            return project_return(
                message="Successfully created.",
                data=client_obj.data,
                status=status.HTTP_201_CREATED,
            )
        else:
            return project_return(
                message="Not created.",
                error=client_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )


class UpdateClientView(GenericAPIView):
    """
    - Client update using first_name, last_name, phone
    - Only ADMINISTRATOR can update CLIENT
    """

    queryset = clientmanage.Client.objects.all()
    serializer_class = serializer.UpdateClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["client"])
    def put(self, request, *args, **kwargs):
        client_query = self.get_queryset().filter(id=kwargs.get("id")).first()
        if not client_query:
            return project_return(
                message="Not updated.",
                error="Client not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not updated.",
                error="Only ADMINISTRATOR can update CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )
        
        client_obj = self.serializer_class(client_query, data=request.data, partial=True)
        if not client_obj.is_valid():
            return project_return(
                message="Not updated.",
                error=client_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.data.get("phone"):
            check_phone = self.get_queryset().filter(
                phone=request.data.get("phone").strip()
            ).exclude(id=str(kwargs.get("id"))).exists()
            if check_phone:
                print("Test")
                return project_return(
                    message="Not updated.",
                    error="Client with this phone number already exists.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        
        client_obj.save()
        return project_return(
            message="Successfully updated.",
            data=client_obj.data,
            status=status.HTTP_200_OK,
        )


