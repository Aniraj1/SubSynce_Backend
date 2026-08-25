from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("authuser.api.urls.admin_urls")),
    path("v1/owner/", include("authuser.api.urls.owner_urls")),
    path("v1/user/", include("authuser.api.urls.user_urls"))
]