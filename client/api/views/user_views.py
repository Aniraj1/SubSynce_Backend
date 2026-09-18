from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema
from client.model import clientmanage
from client.api import serializer
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from globalutils.returnobject import project_return



class UserSiteView(GenericAPIView):
    """
    - Get all sites assigned to the authenticated user
    """

    queryset = clientmanage.Site.objects.all()
    serializer_class = serializer.SiteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @extend_schema(tags=["site"])
    def get(self, request, *args, **kwargs):

        if request.user.role != "CONTRACTOR":
            return project_return(
                message="Failed to fetch.",
                error="Only ADMINISTRATOR can fetch SITE.",
                status=status.HTTP_403_FORBIDDEN,
            )

        filter_obj = self.filter_queryset(self.get_queryset().filter(assigned_contractors=str(request.user.id)))
        data = self.paginate_queryset(filter_obj)
        site_obj = self.serializer_class(data, many=True)
        return project_return(
            message="Successfully fetched.",
            data=self.get_paginated_response(site_obj.data),
            status=status.HTTP_200_OK,
        )