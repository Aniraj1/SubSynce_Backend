from django.urls import path

from work.api.views import user_views

urlpatterns = [
    path("clock-in/", user_views.ClockInView.as_view(), name="ClockInView"),
    path("clock-out/<str:id>/", user_views.ClockOutView.as_view(), name="ClockOutView"),
]