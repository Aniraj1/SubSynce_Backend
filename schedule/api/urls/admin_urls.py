from django.urls import path

from schedule.api.views import admin_views

urlpatterns = [
    path("schedule/", admin_views.ServiceScheduleView.as_view(), name="ServiceScheduleView"),
    path("schedule/<str:id>/", admin_views.ServiceScheduleDetailView.as_view(), name="ServiceScheduleDetailView"),

]