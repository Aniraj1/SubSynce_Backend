from django.urls import path
from decouple import config

from authuser.api.views import admin_views

urlpatterns = [
    path("register/", admin_views.ContractorRegisterView.as_view(), name="ContractorRegisterView"),
    path("list/contractors/", admin_views.ListOfContractorsView.as_view(), name="ListOfContractorsView"),
]
