from django.urls import path

from dashboard.api.views import user_views

urlpatterns = [
	path("dashboard/", user_views.ContractorDashboardView.as_view(), name="ContractorDashboardView"),
]