import pytest
from decouple import config
from django.urls import reverse

from authuser import utils

DEFAULT_PASSWORD = config("SUPER_ADMIN_PASSWORD")


# ------------------- User Login Tests ------------------ #
def test_successful_login(test_user, api_client):
    url = reverse("UserLoginView")
    payload = {
        "username": test_user.username,
        "password": DEFAULT_PASSWORD,
    }

    response = api_client.post(url, payload)
    assert response.status_code == 200

def test_login_with_invalid_user(db, api_client):
    url = reverse("UserLoginView")
    payload = {"username": "test", "password": DEFAULT_PASSWORD}

    response = api_client.post(url, payload)
    assert response.status_code == 404

def test_login_with_invalid_password(test_user, api_client):
    url = reverse("UserLoginView")
    payload = {
        "username": test_user.username,
        "password": f"{DEFAULT_PASSWORD}123",
    }

    response = api_client.post(url, payload)
    assert response.status_code == 401


# ------------------- User Detail Tests ------------------ #
def test_add_user_detail(test_user, login_test_user, api_client):
    url = reverse("UserDetail")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 201


def test_add_user_detail_without_authentication(test_user, api_client):
    url = reverse("UserDetail")
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567890",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 401

def test_add_user_detail_with_invalid_data(test_user, login_test_user, api_client):
    url = reverse("UserDetail")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "first_name": "",
        "last_name": "",
        "phone": "1234567890",
    }
    response = api_client.post(url, payload)
    assert response.status_code == 400


# ------------------- User Detail Update Tests ------------------ #
def test_update_user_detail(test_user, test_user_detail, login_test_user, api_client):
    url = reverse("UserDetail")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "0987654321",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 200

def test_update_user_detail_without_authentication(test_user, test_user_detail, api_client):
    url = reverse("UserDetail")
    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "0987654321",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 401

def test_update_user_detail_with_invalid_data(test_user, test_user_detail, login_test_user, api_client):
    url = reverse("UserDetail")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    payload = {
        "first_name": "",
        "last_name": "",
        "phone": "0987654321",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 400


# -------------------- User Detail Retrieval Tests ------------------ #
def test_get_user_detail(test_user, test_user_detail, login_test_user, api_client):
    url = reverse("UserDetailView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_user_detail_without_authentication(test_user, test_user_detail, api_client):
    url = reverse("UserDetailView")
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_user_detail_with_invalid_token(test_user, test_user_detail, api_client):
    url = reverse("UserDetailView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer invalid_token"
        )
    response = api_client.get(url)
    assert response.status_code == 401


# ------------------- User Logout Tests ------------------ #
def test_user_logout(test_user, login_test_user, api_client):
    url = reverse("UserLogout")
    payload = {"refresh": login_test_user.get("refresh")}
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    response = api_client.post(url, payload)
    assert response.status_code == 200

def test_user_logout_without_authentication(test_user, login_test_user, api_client):
    url = reverse("UserLogout")
    payload = {"refresh": login_test_user.get("refresh")}
    response = api_client.post(url, payload)
    assert response.status_code == 401

def test_user_logout_with_invalid_token(test_user, login_test_user, api_client):
    url = reverse("UserLogout")
    payload = {"refresh": "invalid_token"}
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    response = api_client.post(url, payload)
    assert response.status_code == 400


# ------------------- User Change Password Tests ------------------ #
def test_user_change_password(test_user, login_test_user, api_client):
    url = reverse("LoginUserChangePasswordView")
    payload = {
        "old_password": DEFAULT_PASSWORD,
        "new_password": "NewPassword@123",
    }
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    response = api_client.put(url, payload)
    assert response.status_code == 200

def test_user_change_password_without_authentication(test_user, login_test_user, api_client):
    url = reverse("LoginUserChangePasswordView")
    payload = {
        "old_password": DEFAULT_PASSWORD,
        "new_password": "NewPassword@123",
    }
    response = api_client.put(url, payload)
    assert response.status_code == 401

def test_user_change_password_with_invalid_old_password(test_user, login_test_user, api_client):
    url = reverse("LoginUserChangePasswordView")
    payload = {
        "old_password": "InvalidOldPassword",
        "new_password": "NewPassword@123",
    }
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_user.get('access')}"
        )
    response = api_client.put(url, payload)
    assert response.status_code == 400



# ------------------- Generate Refresh Token Tests ------------------ #
def test_generate_refresh_token(test_user, login_test_user, api_client):
    url = reverse("GenerateTokenFromRefresh")
    payload = {"refresh": login_test_user.get("refresh")}
    response = api_client.post(url, payload)
    assert response.status_code == 200

def test_generate_refresh_token_with_invalid_token(test_user, login_test_user, api_client):
    url = reverse("GenerateTokenFromRefresh")
    payload = {"refresh": "invalid_token"}
    response = api_client.post(url, payload)
    assert response.status_code == 400
