from django.urls import path

from invoice.api.views import admin_views
from dashboard.api.views import admin_views

urlpatterns = [
    path("dashboard/", admin_views.AdminDashboardView.as_view(), name="AdminDashboardView"),
]