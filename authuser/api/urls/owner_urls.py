from django.urls import path

from authuser.api.views import owner_views

urlpatterns = [
    path("register/", owner_views.UserRegister.as_view(), name="UserRegister"),
    path("login/", owner_views.UserLogin.as_view(), name="OwnerLogin"),
    
]
