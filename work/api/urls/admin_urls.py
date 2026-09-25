from django.urls import path

from work.api.views import admin_views

urlpatterns = [
    path("work/", admin_views.AllWorkCompleteView.as_view(), name="AllWorkCompleteView"),
    path("work/summary/", admin_views.AdminWorkSummaryView.as_view(), name="AdminWorkSummaryView"),
    path("work/<str:id>/", admin_views.WorkCompleteDetailView.as_view(), name="WorkCompleteDetailView"),
]