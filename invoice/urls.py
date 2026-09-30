from django.urls import include, path

urlpatterns = [
    path("v1/admin/", include("invoice.api.urls.admin_urls")),
    path("v1/user/", include("invoice.api.urls.user_urls")),
]