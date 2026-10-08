import pytest
from django.urls import reverse

from authuser import utils


# ------------------- Clock In Tests ------------------ #
def test_clock_in(api_client, test_service_schedule, login_test_contractor_user):
    test_service_schedule.status = "SCHEDULED"
    test_service_schedule.save(update_fields=["status"])
    url = reverse("ClockInView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "schedule": test_service_schedule.id,
        "location": "Test Location",
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 201

def test_clock_in_invalid_schedule(api_client, test_service_schedule, login_test_contractor_user):
    url = reverse("ClockInView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "schedule": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa",
        "location": "Test Location",
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 404

def test_clock_in_unauthorized(api_client, test_service_schedule):
    url = reverse("ClockInView")
    payload = {
        "schedule": test_service_schedule.id,
        "location": "Test Location",
    }
    response = api_client.post(url, data=payload)
    assert response.status_code == 401


# ------------------- Clock Out Tests ------------------ #
def test_clock_out(api_client, test_complete_work, login_test_contractor_user):
    url = reverse("ClockOutView", args=[test_complete_work.id])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "completion_notes": "Test Completion Notes",
        "location": "Test Location",
    }
    response = api_client.patch(url, data=payload)
    assert response.status_code == 200

def test_clock_out_invalid_work(api_client, test_complete_work, login_test_contractor_user):
    url = reverse("ClockOutView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    payload = {
        "completion_notes": "Test Completion Notes",
        "location": "Test Location",
    }
    response = api_client.patch(url, data=payload)
    assert response.status_code == 404

def test_clock_out_unauthorized(api_client, test_complete_work):
    url = reverse("ClockOutView", args=[test_complete_work.id])
    payload = {
        "completion_notes": "Test Completion Notes",
        "location": "Test Location",
    }
    response = api_client.patch(url, data=payload)
    assert response.status_code == 401


# ------------------- Get User Work Tests ------------------ #
def test_get_user_work(api_client, test_complete_work, login_test_contractor_user):
    url = reverse("UserWorkView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_user_work_unauthorized(api_client):
    url = reverse("UserWorkView")
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_user_work_with_filters(api_client, test_complete_work, login_test_contractor_user):
    url = reverse("UserWorkView")
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url, data={"status": "IN_PROGRESS"})
    print(response.data)
    assert response.status_code == 200


# ------------------- Get User Work Detail Tests ------------------ #
def test_get_user_work_detail(api_client, test_complete_work, login_test_contractor_user):
    url = reverse("GetDetailWorkView", args=[test_complete_work.id])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_user_work_detail_invalid_work(api_client, test_complete_work, login_test_contractor_user):
    url = reverse("GetDetailWorkView", args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 404

def test_get_user_work_detail_unauthorized(api_client, test_complete_work):
    url = reverse("GetDetailWorkView", args=[test_complete_work.id])
    response = api_client.get(url)
    assert response.status_code == 401