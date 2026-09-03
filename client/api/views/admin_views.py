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


class ClientView(GenericAPIView):
    """
    - Client register using first_name, last_name, phone, email
    - Only ADMINISTRATOR can create CLIENT
    """

    queryset = clientmanage.Client.objects.all()
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

    @extend_schema(tags=["client"])
    def get(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )
        filter_obj = self.filter_queryset(self.get_queryset())
        data = self.paginate_queryset(filter_obj)
        client_obj = self.serializer_class(data, many=True)
        return project_return(
            message="Successfully fetched.",
            data=self.get_paginated_response(client_obj.data),
            status=status.HTTP_200_OK,
        )
        


class UpdateClientView(GenericAPIView):
    """
    - Client update using first_name, last_name, phone
    - delete client using id
    - Only ADMINISTRATOR can update CLIENT
    """

    queryset = clientmanage.Client.objects.all()
    serializer_class = serializer.UpdateClientSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["client"])
    def get(self, request, *args, **kwargs):
        client_query = self.get_queryset().filter(id=kwargs.get("id")).first()
        if not client_query:
            return project_return(
                message="Not fetched.",
                error="Client not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_obj = self.serializer_class(client_query)
        return project_return(
            message="Successfully fetched.",
            data=client_obj.data,
            status=status.HTTP_200_OK,
        )

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

    @extend_schema(tags=["client"])
    def delete(self, request, *args, **kwargs):
        client_query = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not client_query:
            return project_return(
                message="Not deleted.",
                error="Client not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not deleted.",
                error="Only ADMINISTRATOR can delete CLIENT.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_query.delete()
        return project_return(
            message="Successfully deleted.",
            status=status.HTTP_200_OK,
        )




class SiteView(GenericAPIView):
    """
    - Site register using name, address, cleaning_frequency, price, client_id, cleaning_instructions
    - Only ADMINISTRATOR can create SITE
    """

    queryset = clientmanage.Site.objects.all()
    serializer_class = serializer.SiteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["site"])
    def post(self, request, *args, **kwargs):
        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not created.",
                error="Only ADMINISTRATOR can create SITE.",
                status=status.HTTP_403_FORBIDDEN,
            )

        client_id = request.data.get("client_id")
        if not client_id or not clientmanage.Client.objects.filter(id=client_id).exists():
            return project_return(
                message="Not created.",
                error="Client not found.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        payload = request.data.copy()
        files = request.FILES.getlist("site_image")
        if files:
            payload.setlist("site_image", files)

        site_obj = self.serializer_class(data=payload)
        if site_obj.is_valid():
            site = site_obj.save()
            return project_return(
                message="Successfully created.",
                data=self.serializer_class(site).data,
                status=status.HTTP_201_CREATED,
            )

        return project_return(
            message="Not created.",
            error=site_obj.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class UpdateSiteView(GenericAPIView):
    """
    - Site update using name, address, cleaning_frequency, price, client_id, cleaning_instructions
    - delete site using id
    - Only ADMINISTRATOR can update SITE
    """

    queryset = clientmanage.Site.objects.all()
    serializer_class = serializer.UpdateSiteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["site"])
    def put(self, request, *args, **kwargs):
        site_query = self.get_queryset().filter(id=kwargs.get("id")).first()
        if not site_query:
            return project_return(
                message="Not updated.",
                error="Site not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not updated.",
                error="Only ADMINISTRATOR can update SITE.",
                status=status.HTTP_403_FORBIDDEN,
            )

        site_obj = self.serializer_class(site_query, data=request.data, partial=True)
        if not site_obj.is_valid():
            return project_return(
                message="Not updated.",
                error=site_obj.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        site_obj.save()
        return project_return(
            message="Successfully updated.",
            data=site_obj.data,
            status=status.HTTP_200_OK,
        )


    @extend_schema(tags=["site"])
    def delete(self, request, *args, **kwargs):
        site_query = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not site_query:
            return project_return(
                message="Not deleted.",
                error="Site not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not deleted.",
                error="Only ADMINISTRATOR can delete SITE.",
                status=status.HTTP_403_FORBIDDEN,
            )

        site_query.delete()
        return project_return(
            message="Successfully deleted.",
            status=status.HTTP_200_OK,
        )




class GetSiteView(GenericAPIView):
    """
    - Get site details using id
    - Only ADMINISTRATOR can fetch SITE
    """
    queryset = clientmanage.Site.objects.all()
    serializer_class = serializer.GetSiteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    
    @extend_schema(tags=["site"])
    def get(self, request, *args, **kwargs):
        site_query = self.get_queryset().filter(id=str(kwargs.get("id"))).first()
        if not site_query:
            return project_return(
                message="Not fetched.",
                error="Site not found.",
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role != "ADMINISTRATOR":
            return project_return(
                message="Not fetched.",
                error="Only ADMINISTRATOR can fetch SITE.",
                status=status.HTTP_403_FORBIDDEN,
            )

        site_obj = self.serializer_class(site_query)
        return project_return(
            message="Successfully fetched.",
            data=site_obj.data,
            status=status.HTTP_200_OK,
        )
