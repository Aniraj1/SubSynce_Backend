from rest_framework.generics import GenericAPIView
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from authuser import models, utils
from authuser.api.serializer import UserRegisterSerializer
from django.core.exceptions import ValidationError
from rest_framework import status

from globalutils.returnobject import project_return





class UserRegister(GenericAPIView):
    """
    - User register using username, email, password and phone(optional)
    """

    queryset = models.User
    serializer_class = UserRegisterSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(tags=["authuser"])
    def post(self, request, *args, **kwargs):
        user_obj = self.serializer_class(data=request.data)

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
