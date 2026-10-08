import pytest
from decouple import config
from django.urls import reverse

from authuser import utils



# ------------------- Admin Dashboard Tests ------------------ #
def test_get_admin_dashboard_success(api_client, test_site, test_service_schedule, test_complete_work, test_contractor_invoice, login_test_admin_user):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user['access']}")
    url = reverse("AdminDashboardView")
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_admin_dashboard_unauthorized(api_client):
    url = reverse("AdminDashboardView")
    response = api_client.get(url)
    assert response.status_code == 401