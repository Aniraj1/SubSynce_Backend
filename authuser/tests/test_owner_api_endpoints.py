import pytest
from decouple import config
from django.urls import reverse

from authuser import utils

DEFAULT_PASSWORD = config("SUPER_ADMIN_PASSWORD")


# ------------------- User Register Tests ------------------ #
def test_owner_register_user(test_user, login_test_user, api_client):
    url = reverse("UserRegister")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "username": "john_doe",
        "email": "john.doe@example.com",
        "password": DEFAULT_PASSWORD,
        "role": "ADMINISTRATOR",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 201

def test_owner_register_user_with_existing_email(test_user, login_test_user, api_client):
    url = reverse("UserRegister")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "username": "jane_doe",
        "email": test_user.email,  # Use the email of the existing test user
        "password": DEFAULT_PASSWORD,
        "role": "CONTRACTOR",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 400

def test_owner_register_user_with_invalid_role(test_user, login_test_user, api_client):
    url = reverse("UserRegister")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "username": "alice_smith",
        "email": "alice.smith@example.com",
        "password": DEFAULT_PASSWORD,
        "role": "INVALID_ROLE",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 400
