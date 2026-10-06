import pytest
from decouple import config
from django.urls import reverse

from authuser import utils




#------------------- Add Client Tests ------------------ #
def test_add_client(login_test_admin_user, api_client):
    url = reverse("ClientView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "email": "john.doe@example.com",
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 201


def test_add_client_without_authentication(api_client):
    url = reverse("ClientView")
    payload = {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "email": "john.doe@example.com",
        }
    response = api_client.post(url, data=payload)
    assert response.status_code == 401

def test_add_client_with_contractor_user(login_test_contractor_user, api_client):
    url = reverse("ClientView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    payload = {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "email": "john.doe@example.com",
            }
    response = api_client.post(url, data=payload)
    assert response.status_code == 403



# ------------------- Client List Tests ------------------ #
def test_list_of_clients(login_test_admin_user, test_client, api_client):
    url = reverse("ClientView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 200


def test_list_of_clients_without_authentication(test_client, api_client):
    url = reverse("ClientView")
    response = api_client.get(url)
    assert response.status_code == 401


def test_list_of_clients_with_contractor_user(login_test_contractor_user, test_client, api_client):
    url = reverse("ClientView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 403


# ------------------- Client Detail Tests ------------------ #
def test_get_client_detail(login_test_admin_user, test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_client_detail_without_authentication(test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_client_detail_with_contractor_user(login_test_contractor_user, test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 403

def test_get_client_detail_with_invalid_client_id(login_test_admin_user, api_client):
    url = reverse("UpdateClientView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 404


# ------------------- Client Update Tests ------------------ #
def test_update_client(login_test_admin_user, test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    payload = {
        "first_name": "Jane",
        "last_name": "Smith",
        "phone": "+0987654321",
        "email": "jane.smith@example.com"
    }
    response = api_client.put(url, data=payload)
    assert response.status_code == 200

def test_update_client_without_authentication(test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    payload = {
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+0987654321",
            "email": "jane.smith@example.com"
        }
    response = api_client.put(url, data=payload)
    assert response.status_code == 401

def test_update_client_with_contractor_user(login_test_contractor_user, test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    payload = {
                "first_name": "Jane",
                "last_name": "Smith",
                "phone": "+0987654321",
                "email": "jane.smith@example.com"
            }
    response = api_client.put(url, data=payload)
    assert response.status_code == 403

def test_update_client_with_invalid_client_id(login_test_admin_user, api_client):
    url = reverse("UpdateClientView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    payload = {
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "phone": "+0987654321",
                    "email": "jane.smith@example.com"
                }
    response = api_client.put(url, data=payload)
    assert response.status_code == 404


# ------------------- Client Delete Tests ------------------ #
def test_delete_client(login_test_admin_user, test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.delete(url)
    assert response.status_code == 200

def test_delete_client_without_authentication(test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    response = api_client.delete(url)
    assert response.status_code == 401

def test_delete_client_with_contractor_user(login_test_contractor_user, test_client, api_client):
    url = reverse("UpdateClientView", args=[str(test_client.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    response = api_client.delete(url)
    assert response.status_code == 403

def test_delete_client_with_invalid_client_id(login_test_admin_user, api_client):
    url = reverse("UpdateClientView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.delete(url)
    assert response.status_code == 404


# ------------------- Add Site Tests ------------------ #
def test_add_site(login_test_admin_user, test_client, test_contractor_user, api_client):
    url = reverse("SiteView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    payload = {
        "name": "Site A",
        "address": "123 Main St",
        "cleaning_frequency": 7,
        "price": 100.0,
        "client_id": str(test_client.id),
        "cleaning_instructions": "Clean thoroughly.",
        "assigned_contractor": str(test_contractor_user.id)
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 201

def test_add_site_without_authentication(test_client, test_contractor_user, api_client):
    url = reverse("SiteView")
    payload = {
            "name": "Site A",
            "address": "123 Main St",
            "cleaning_frequency": 7,
            "price": 100.0,
            "client_id": str(test_client.id),
            "cleaning_instructions": "Clean thoroughly.",
            "assigned_contractor": str(test_contractor_user.id)
        }
    response = api_client.post(url, data=payload)
    assert response.status_code == 401

def test_add_site_with_contractor_user(login_test_contractor_user, test_client, test_contractor_user, api_client):
    url = reverse("SiteView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    payload = {
                "name": "Site A",
                "address": "123 Main St",
                "cleaning_frequency": 7,
                "price": 100.0,
                "client_id": str(test_client.id),
                "cleaning_instructions": "Clean thoroughly.",
                "assigned_contractor": str(test_contractor_user.id)
            }
    response = api_client.post(url, data=payload)
    assert response.status_code == 403

def test_add_site_with_invalid_client_id(login_test_admin_user, test_contractor_user, api_client):
    url = reverse("SiteView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    payload = {
                "name": "Site A",
                "address": "123 Main St",
                "cleaning_frequency": 7,
                "price": 100.0,
                "client_id": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa",
                "cleaning_instructions": "Clean thoroughly.",
                "assigned_contractor": str(test_contractor_user.id)
            }
    response = api_client.post(url, data=payload)
    assert response.status_code == 400



# ------------------- Site List Tests ------------------ #
def test_list_of_sites(login_test_admin_user, test_site, api_client):
    url = reverse("SiteView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_list_of_sites_without_authentication(test_site, api_client):
    url = reverse("SiteView")
    response = api_client.get(url)
    assert response.status_code == 401

def test_list_of_sites_with_contractor_user(login_test_contractor_user, test_site, api_client):
    url = reverse("SiteView")
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 403


# ------------------- Site Detail Tests ------------------ #
def test_get_site_detail(login_test_admin_user, test_site, api_client):
    url = reverse("UpdateSiteView", args=[str(test_site.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_site_detail_with_invalid_site_id(login_test_admin_user, api_client):
    url = reverse("UpdateSiteView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 404

def test_get_site_detail_without_authentication(test_site, api_client):
    url = reverse("UpdateSiteView", args=[str(test_site.id)])
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_site_detail_with_contractor_user(login_test_contractor_user, test_site, api_client):
    url = reverse("UpdateSiteView", args=[str(test_site.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_contractor_user.get('access')}"
        )
    response = api_client.get(url)
    assert response.status_code == 403



# ------------------- Site Delete Tests ------------------ #
def test_delete_site(login_test_admin_user, test_site, api_client):
    url = reverse("UpdateSiteView", args=[str(test_site.id)])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.delete(url)
    assert response.status_code == 200

def test_delete_site_with_invalid_site_id(login_test_admin_user, api_client):
    url = reverse("UpdateSiteView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_test_admin_user.get('access')}"
        )
    response = api_client.delete(url)
    assert response.status_code == 404

def test_delete_site_without_authentication(test_site, api_client):
    url = reverse("UpdateSiteView", args=[str(test_site.id)])
    response = api_client.delete(url)
    assert response.status_code == 401
