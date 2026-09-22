from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("schedule.api.urls.admin_urls")),
    path("v1/user/", include("schedule.api.urls.user_urls")),
]