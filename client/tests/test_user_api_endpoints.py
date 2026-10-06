import pytest
from decouple import config
from django.urls import reverse

from authuser import utils




# ------------------- UserSite Tests ------------------ #
def test_user_sites(test_site, test_contractor_user, login_test_contractor_user, api_client):
    url = reverse("UserSiteView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_user_sites_without_authentication(test_site, api_client):
    url = reverse("UserSiteView")
    response = api_client.get(url)
    assert response.status_code == 401

def test_user_sites_with_admin_user(test_site, login_test_admin_user, api_client):
    url = reverse("UserSiteView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 403