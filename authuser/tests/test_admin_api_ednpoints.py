import pytest
from decouple import config
from django.urls import reverse

from authuser import utils

DEFAULT_PASSWORD = config("SUPER_ADMIN_PASSWORD")



# ------------------- Contractor Registration Tests ------------------ #
def test_contractor_register(login_test_admin_user, api_client):
    url = reverse("ContractorRegisterView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    payload = {
        "username": "contractor_user",
        "password": DEFAULT_PASSWORD,
        "email": "contractor_user@example.com",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 201

def test_contractor_register_owners_email(login_test_user, api_client):
    url = reverse("ContractorRegisterView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "username": "contractor_user",
        "password": DEFAULT_PASSWORD,
        "email": "contractor_user@example.com",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 403

def test_contractor_register_existing_email(login_test_admin_user, api_client, test_admin_user):
    url = reverse("ContractorRegisterView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    payload = {
        "username": "contractor_user",
        "password": DEFAULT_PASSWORD,
        "email": test_admin_user.email,
    }
    response = api_client.post(url, payload)
    assert response.status_code == 400


# ------------------- List of Contractors Tests ------------------ #
def test_list_of_contractors(test_contractor_user, login_test_admin_user, api_client):
    url = reverse("ListOfContractorsView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_list_of_contractors_not_admin(test_contractor_user, login_test_user, api_client):
    url = reverse("ListOfContractorsView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 403

def test_list_of_contractors_no_auth(test_contractor_user, api_client):
    url = reverse("ListOfContractorsView")
    response = api_client.get(url)
    assert response.status_code == 401
