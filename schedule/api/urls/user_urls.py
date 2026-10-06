from django.urls import path

from schedule.api.views import user_views

urlpatterns = [
    path("schedule/", user_views.UserScheduleView.as_view(), name="UserScheduleView"),
    path("schedule/summary/", user_views.UserScheduleSummaryView.as_view(), name="UserScheduleSummaryView"),
    path("schedule/<str:id>/", user_views.GetDetailScheduleView.as_view(), name="GetDetailScheduleView"),

]