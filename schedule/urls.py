from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("schedule.api.urls.admin_urls")),
]