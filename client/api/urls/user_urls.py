from django.urls import path
from decouple import config

from client.api.views import user_views

urlpatterns = [
    path("user-sites/", user_views.UserSiteView.as_view(), name="UserSiteView"),
]
