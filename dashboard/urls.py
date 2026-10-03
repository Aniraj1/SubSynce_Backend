from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("dashboard.api.urls.admin_urls")),
    path("v1/user/", include("dashboard.api.urls.user_urls")),
]