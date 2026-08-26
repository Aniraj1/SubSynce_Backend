from rest_framework.generics import GenericAPIView
from rest_framework.throttling import AnonRateThrottle
from drf_spectacular.utils import extend_schema
from authuser import models, utils
from authuser.api import serializer
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
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


        return project_return(
            message="Successfully logged in." if user else "Not logged in.",
            data= {"token": return_credentials, "role": check_username.role },
            status=status.HTTP_200_OK if user else status.HTTP_401_UNAUTHORIZED,
        )


class UserDetail(GenericAPIView):
    """
    - User detail using access token
    - User can post and update first name, last name and phone number
    """
    queryset = models.UserDetail
    serializer_class = serializer.UserDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]


    @extend_schema(tags=["authuser"])
    def post(self, request, *args, **kwargs):
        user_obj = self.serializer_class(data=request.data)
        
        if not request.data.get("first_name") or not request.data.get("last_name"):
            return project_return(
                message="Validation error.",
                error="First name and last name are required.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not user_obj.is_valid():
            return project_return(
                message="Validation error.",
                error=user_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if models.UserDetail.objects.filter(user=request.user).first():
            return project_return(
                message="User detail already exists.",
                error="Unable to post with this user.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_obj.save(user=request.user)
        return project_return(
            message="Successfully created.",
            data=user_obj.data,
            status=status.HTTP_201_CREATED,
        )
        
    
    @extend_schema(tags=["authuser"])
    def put(self, request, *args, **kwargs):
        user_detail_obj = models.UserDetail.objects.filter(
            user=request.user
        ).first()
        user_obj = self.serializer_class(
            user_detail_obj, data=request.data, partial=True
        )

        if not request.data.get("first_name") or not request.data.get("last_name"):
            return project_return(
                message="Validation error.",
                error="First name and last name are required.",
                status=status.HTTP_400_BAD_REQUEST,
            ) 

        if user_obj.is_valid():
            user_obj.save()
            return project_return(
                message="Successfully updated.",
                data=user_obj.data,
                status=status.HTTP_200_OK,
            )
        return project_return(
            message="Validation error.",
            error=user_obj.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

class UserDetailView(GenericAPIView):
    """
    - Get user detail using access token
    """
    queryset = models.User
    serializer_class = serializer.UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["authuser"])
    def get(self, request, *args, **kwargs):
        user_obj = self.serializer_class(
            self.get_queryset().objects.filter(id=request.user.id).first()  
        )
        return project_return(
            message="Successfully fetched.",
            data=user_obj.data,
            status=status.HTTP_200_OK,
        )
    

class UserLogout(GenericAPIView):
    """
    - logouts out user and invalidate access and refresh tokens
    """
    serializer_class = serializer.TokenSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["authuser"])
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return project_return(
                message="Refresh token is required.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return project_return(
                message="Successfully logged out.",
                status=status.HTTP_200_OK,
            )
        except TokenError as e:
            return project_return(
                message="Token is invalid or already expired.",
                error=e.args,
                status=status.HTTP_400_BAD_REQUEST,
            )

class GenerateTokenFromRefresh(TokenViewBase):
    """
    Renew tokens (access and refresh) with new expire time based
    on specific user's access token.
    """

    serializer_class = TokenRefreshSerializer
    throttle_classes = [AnonRateThrottle]

    @extend_schema(tags=["authuser"])
    def post(self, request, *args, **kwargs):
        token_obj = self.get_serializer(data=request.data)
        if not request.data.get("refresh"):
            return project_return(
                message="Refresh token is required.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token_obj.is_valid(raise_exception=True)
        except TokenError as e:
            return project_return(
                message="Token Error.",
                error=e.args[0],
                status=status.HTTP_400_BAD_REQUEST,
            )
        return project_return(
            message="Successfully generated.",
            data=token_obj.validated_data,
            status=status.HTTP_200_OK,
        )

    
class LoginUserChangePasswordView(GenericAPIView):
    queryset = models.User
    serializer_class = serializer.LoginUserChangePasswordSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["authuser"])
    def put(self, request, *args, **kwargs):
        request_obj = self.serializer_class(data=request.data)
        if not request_obj.is_valid():
            return project_return(
                message="Invalid data.",
                error=request_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        check_old_password = authenticate(
            username=request.user.username,
            password=request.data.get("old_password"),
        )
        if not check_old_password:
            return project_return(
                message="Invalid old password.",
                error="The old password does not match.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(password=request.data.get("new_password"))
        except ValidationError as e:
            return project_return(
                message="Invalid password format.",
                error=e.args,
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.password = make_password(request.data.get("new_password"))
        request.user.save()

        return project_return(
            message="Password changed successfully.", status=status.HTTP_200_OK
        )