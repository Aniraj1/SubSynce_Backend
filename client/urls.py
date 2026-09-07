from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("client.api.urls.admin_urls")),
]