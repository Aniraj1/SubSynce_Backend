from django.urls import path
from decouple import config

from client.api.views import admin_views

urlpatterns = [
    path("client/", admin_views.ClientView.as_view(), name="ClientView"),
    path("client/<str:id>/", admin_views.UpdateClientView.as_view(), name="UpdateClientView"),
    path("site/", admin_views.SiteView.as_view(), name="SiteView"),
    path("site/<str:id>/", admin_views.UpdateSiteView.as_view(), name="UpdateSiteView"),
    path("site-details/<str:id>/", admin_views.GetSiteView.as_view(), name="GetSiteView"),
]
