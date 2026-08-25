from rest_framework.generics import GenericAPIView
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema
from authuser import models, utils
from authuser.api import serializer
from rest_framework import status
from django.contrib.auth import authenticate
from globalutils.returnobject import project_return




class UserLogin(GenericAPIView):
    """
    - User login using username and password and return access and refresh token
    """

    queryset = models.User
    serializer_class = serializer.UserLoginSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(tags=["authuser"])
    def post(self, request, *args, **kwargs):
        request_obj = self.serializer_class(data=request.data)
        if not request_obj.is_valid():
            return project_return(
                message="Not logged in.",
                error=request_obj.errors,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = authenticate(
            username=request.data.get("username"),
            password=request.data.get("password"),
        )

        return_credentials = utils.get_tokens_for_user(user) if user else None


        check_username = models.User.objects.filter(
            username=request.data.get("username")
        ).first()

        if not check_username:
            return project_return(
                message="User does not exist.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if check_username.role != "CONTRACTOR":
            return project_return(
                message="User does not exists.",
                status=status.HTTP_403_FORBIDDEN,
            )


        return project_return(
            message="Successfully logged in." if user else "Not logged in.",
            data= return_credentials,
            status=status.HTTP_200_OK if user else status.HTTP_401_UNAUTHORIZED,
        )