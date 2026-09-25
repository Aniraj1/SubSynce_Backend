from django.urls import path

from work.api.views import user_views

urlpatterns = [
    path("clock-in/", user_views.ClockInView.as_view(), name="ClockInView"),
    path("clock-out/<str:id>/", user_views.ClockOutView.as_view(), name="ClockOutView"),
    path("work/", user_views.UserWorkView.as_view(), name="UserWorkView"),
    path("work/<str:id>/", user_views.GetDetailWorkView.as_view(), name="GetDetailWorkView"),
]