from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("work.api.urls.admin_urls")),
    path("v1/user/", include("work.api.urls.user_urls")),
]