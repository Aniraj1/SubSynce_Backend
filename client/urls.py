from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("client.api.urls.admin_urls")),
    path("v1/user/", include("client.api.urls.user_urls"))
]