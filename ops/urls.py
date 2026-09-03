from django.urls import path
from . import views

# App namespace - allows us to use 'ops:login', 'ops:dashboard', etc.
app_name = 'ops'

urlpatterns = [
    # Login page (root URL)
    path('', views.login_view, name='login'),
    
    # Dashboard (protected - requires login)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),
]
