from django.urls import path

from authuser.api.views import user_views

urlpatterns = [
    path("login/", user_views.UserLogin.as_view(), name="UserLoginView"),
    path("user-detail/", user_views.UserDetail.as_view(), name="UserDetail"),
    path("user-info/", user_views.UserDetailView.as_view(), name="UserDetailView"),
    path("logout/", user_views.UserLogout.as_view(), name="UserLogout"),
    path("/refresh-token/", user_views.GenerateTokenFromRefresh.as_view(), name="GenerateTokenFromRefresh"),
    path("logged-in-user/change-password/", user_views.LoginUserChangePasswordView.as_view(), name="LoginUserChangePasswordView"),

]
