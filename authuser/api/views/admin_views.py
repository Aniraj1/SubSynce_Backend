from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from authuser import models, utils
from authuser.api import serializer
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from globalutils.returnobject import project_return





class ContractorRegisterView(GenericAPIView):
    """
    - Contractor register using username, email, password
    - Only ADMINISTRATOR can create CONTRACTOR
    """

    queryset = models.User
    serializer_class = serializer.ContractorRegisterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["authuser"])
    def post(self, request, *args, **kwargs):
        user_obj = self.serializer_class(data=request.data)
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not created.",
                error="Only ADMINISTRATOR can create CONTRACTOR.",
                status=status.HTTP_403_FORBIDDEN,
            )
        if user_obj.is_valid():
            try:
                validate_password(password=request.data.get("password"))
            except ValidationError as e:
                return project_return(
                    message="Not created.",
                    error=e.args,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            check_email = models.User.objects.filter(
                email=request.data.get("email")
            )
            if check_email:
                return project_return(
                    message="Not created.",
                    error="User with this email already exists.",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_obj.save(
                password=make_password(password=request.data.get("password")),
            )

            return project_return(
                message="Successfully created.",
                data=utils.get_tokens_for_user(
                    models.User.objects.get(id=user_obj.data.get("id"))
                ),
                status=status.HTTP_201_CREATED,
            )


        return project_return(
            message="Not created.",
            error=user_obj.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )



class ListOfContractorsView(GenericAPIView):
    """
    - List of all contractors
    - Only ADMINISTRATOR can view list of CONTRACTOR
    """

    queryset = models.User.objects.filter(role="CONTRACTOR")
    serializer_class = serializer.ListOfContractorsSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["authuser"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(  
                message="Not allowed.",
                error="Only ADMINISTRATOR can view list of CONTRACTOR.",
                status=status.HTTP_403_FORBIDDEN,
            )

        filter_obj = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(filter_obj)
        contractor_obj = self.serializer_class(data, many=True)
        return project_return(
            message="Successfully fetched.",
            data=self.get_paginated_response(contractor_obj.data),
            status=status.HTTP_200_OK,
        )