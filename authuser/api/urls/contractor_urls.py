from django.urls import path
from decouple import config

from authuser.api.views import contractor_views

urlpatterns = [
    path("login/", contractor_views.UserLogin.as_view(), name="ContractorLoginView"),
    
]
