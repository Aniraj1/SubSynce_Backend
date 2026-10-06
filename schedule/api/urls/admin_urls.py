from django.urls import path

from schedule.api.views import admin_views

urlpatterns = [
    path("schedule/", admin_views.ServiceScheduleView.as_view(), name="ServiceScheduleView"),
    path("schedule/summary/", admin_views.ScheduleSummary.as_view(), name="ScheduleSummary"),
    path("schedule/<str:id>/", admin_views.ServiceScheduleDetailView.as_view(), name="ServiceScheduleDetailView"),
    path("schedule/<str:id>/status/", admin_views.ChangeStatusView.as_view(), name="ChangeStatusView"),
]