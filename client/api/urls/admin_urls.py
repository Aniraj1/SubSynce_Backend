from django.urls import path
from decouple import config

from client.api.views import admin_views

urlpatterns = [
    path("add-client/", admin_views.AddClientView.as_view(), name="AddClientView"),
    path("update-client/<str:id>/", admin_views.UpdateClientView.as_view(), name="UpdateClientView"),
]
